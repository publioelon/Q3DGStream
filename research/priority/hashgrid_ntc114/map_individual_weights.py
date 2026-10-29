#!/usr/bin/env python3
"""Map retained HashGrid weights to Gaussians and measure their motion influence."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import q3dg_paths as paths
from map_gaussian_blocks import BLOCK, HASH_BLOCKS, HASH_PARAMS, encoding_layout


def weight_accesses(coords, layout, features, interpolation, primes, retained):
    """Return Gaussian IDs, global weight IDs, and interpolation coefficients."""
    n = len(coords)
    if not n:
        return np.empty(0, np.uint32), np.empty(0, np.int32), np.empty(0, np.float32)
    coords = np.asarray(coords, dtype=np.float32)
    if coords.shape != (n, 3) or not np.isfinite(coords).all():
        raise ValueError("Expected finite normalized XYZ coordinates")
    if retained.shape != (HASH_BLOCKS,) or retained.dtype != np.bool_:
        raise ValueError("Invalid retained block mask")
    gids, wids, coeffs = [], [], []
    channels = np.arange(features, dtype=np.int64)
    for _, offset, entries, resolution, scale in layout:
        scaled = (coords * np.float32(scale) + np.float32(0.5)).astype(np.float32)
        floored = np.floor(scaled)
        grid = floored.astype(np.int64)
        fraction = scaled - floored
        for corner in range(1 if interpolation == "nearest" else 8):
            dx, dy, dz = corner & 1, (corner >> 1) & 1, (corner >> 2) & 1
            if interpolation == "nearest":
                dx = dy = dz = 0
                coefficient = np.ones(n, dtype=np.float32)
            else:
                # Each grid vertex shares one coefficient across its features.
                coefficient = ((fraction[:, 0] if dx else 1 - fraction[:, 0]) *
                               (fraction[:, 1] if dy else 1 - fraction[:, 1]) *
                               (fraction[:, 2] if dz else 1 - fraction[:, 2]))
            active = np.flatnonzero(coefficient > 0)
            if not len(active):
                continue
            x = grid[active, 0].astype(np.uint64) + np.uint64(dx)
            y = grid[active, 1].astype(np.uint64) + np.uint64(dy)
            z = grid[active, 2].astype(np.uint64) + np.uint64(dz)
            if resolution <= 1625 and entries >= resolution**3:
                index = (x + y * np.uint64(resolution) +
                         z * np.uint64(resolution**2)) % np.uint64(entries)
            else:
                index = ((x * np.uint64(primes[0])) ^
                         (y * np.uint64(primes[1])) ^
                         (z * np.uint64(primes[2]))) & np.uint64(0xffffffff)
                index %= np.uint64(entries)
            base = (np.uint64(offset) + index) * np.uint64(features)
            take = retained[(base // np.uint64(BLOCK)).astype(np.int64)]
            if not np.any(take):
                continue
            g = active[take]
            b = base[take].astype(np.int64)
            gids.append(np.repeat(g, features).astype(np.uint32))
            wids.append((b[:, None] + channels).ravel().astype(np.int32))
            coeffs.append(np.repeat(coefficient[g], features).astype(np.float32))
    if not gids:
        return np.empty(0, np.uint32), np.empty(0, np.int32), np.empty(0, np.float32)
    return np.concatenate(gids), np.concatenate(wids), np.concatenate(coeffs)


def merge_weight_pairs(gaussian_ids, weight_ids, coefficients, count):
    """Sum coefficients when hash collisions repeat a weight for one Gaussian."""
    if not len(weight_ids):
        return np.empty(0, np.uint64), np.empty(0, np.float32)
    keys = (weight_ids.astype(np.uint64) * np.uint64(count) +
            gaussian_ids.astype(np.uint64))
    perm = np.argsort(keys, kind="stable")
    keys, coefficients = keys[perm], coefficients[perm]
    first = np.r_[0, np.flatnonzero(keys[1:] != keys[:-1]) + 1]
    totals = np.add.reduceat(coefficients.astype(np.float64), first)
    return keys[first], totals.astype(np.float32)


def make_csr(coords, within_bounds, layout, features, interpolation, primes,
             retained_blocks, batch, progress=False):
    """Build a sparse weight-to-Gaussian lookup without a dense Jacobian."""
    n = len(coords)
    mask = np.zeros(HASH_BLOCKS, dtype=np.bool_)
    mask[retained_blocks] = True
    pieces, coeffs = [], []
    for beg in range(0, n, batch):
        end = min(beg + batch, n)
        valid = np.flatnonzero(within_bounds[beg:end])
        if not len(valid):
            continue
        g, w, c = weight_accesses(coords[beg:end][valid], layout, features,
                                  interpolation, primes, mask)
        global_ids = (beg + valid[g]).astype(np.uint32)
        keys, values = merge_weight_pairs(global_ids, w, c, n)
        pieces.append(keys)
        coeffs.append(values)
        if progress and (end == n or end % (batch * 16) == 0):
            print(f"[INDEX] {end:,}/{n:,} Gaussians", flush=True)
    if not pieces:
        raise ValueError("No retained HashGrid weights were accessed")
    keys = np.concatenate(pieces)
    values = np.concatenate(coeffs)
    # Each Gaussian belongs to exactly one chunk.
    perm = np.argsort(keys)
    keys, values = keys[perm], values[perm]
    if np.any(keys[1:] == keys[:-1]):
        raise AssertionError("Unexpected duplicate across chunks")
    weights = np.sort((retained_blocks[:, None] * BLOCK +
                       np.arange(BLOCK, dtype=np.int64)).ravel()).astype(np.int32)
    active = (keys // np.uint64(n)).astype(np.int32)
    rows = np.searchsorted(weights, active)
    if np.any(rows >= len(weights)) or not np.array_equal(weights[rows], active):
        raise AssertionError("Unexpected weight outside the retained HashGrid")
    counts = np.bincount(rows, minlength=len(weights)).astype(np.int64)
    offsets = np.r_[0, counts.cumsum()]
    return weights, offsets, (keys % np.uint64(n)).astype(np.int32), values


def cuda_check(cfg, coords, within_bounds, layout, features, interp, primes,
               retained_blocks, probes, seed=114):
    """Compare individual-weight support against tiny-cuda-nn gradients."""
    import torch
    import tinycudann as tcnn
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for individual-weight verification")
    enc = tcnn.Encoding(n_input_dims=3, encoding_config=cfg).cuda().train()
    if enc.params.numel() != HASH_PARAMS:
        raise RuntimeError("Installed tiny-cuda-nn uses a different HashGrid layout")
    mask = np.zeros(HASH_BLOCKS, np.bool_)
    mask[retained_blocks] = True
    permitted = np.repeat(mask, BLOCK)
    candidates = np.flatnonzero(within_bounds)
    if not len(candidates):
        raise ValueError("No in-bounds Gaussians")
    selected = np.random.default_rng(seed).choice(
        candidates, min(probes, len(candidates)), replace=False)
    for gid in selected:
        xyz = coords[gid:gid + 1]
        g, wid, c = weight_accesses(xyz, layout, features, interp, primes, mask)
        expected, coefficients = merge_weight_pairs(g, wid, c, 1)
        enc.zero_grad(set_to_none=True)
        x = torch.from_numpy(np.repeat(xyz, 128, axis=0)).cuda()
        enc(x).float().sum().backward()
        grad = enc.params.grad
        if grad is None:
            raise RuntimeError("tiny-cuda-nn returned no encoding gradients")
        observed = np.flatnonzero((grad.detach().float().cpu().numpy() != 0) & permitted)
        if not np.array_equal(expected, observed.astype(np.uint64)):
            missing = np.setdiff1d(expected, observed)
            extra = np.setdiff1d(observed, expected)
            raise RuntimeError(
                f"Gaussian {gid}: individual index mismatch; "
                f"expected-only={missing[:12]}, GPU-only={extra[:12]}")
        if not len(coefficients):
            raise AssertionError("Empty interpolation coefficient set")
        print(f"[CUDA] Gaussian {gid}: {len(observed)} individual indices match",
              flush=True)
    print(f"[CUDA PASS] {len(selected)}/{len(selected)} weight-level index checks",
          flush=True)


def decode_wire(wire):
    """Decode the stored sparse INT4 weights without changing the checkpoint."""
    sys.path.insert(0, str(ROOT / "research/priority/dynamic_299"))
    from qntc_progressive_wire import extract_records_from_torch, decode_records_into, TOTAL
    full = np.zeros((TOTAL, BLOCK), dtype=np.float32)
    decode_records_into(full, extract_records_from_torch(wire))
    return full.reshape(-1)


def infer(model, coords, batch):
    """Evaluate predicted translation and quaternion outputs in small batches."""
    import torch
    result = []
    with torch.no_grad():
        for beg in range(0, len(coords), batch):
            selected = np.ascontiguousarray(coords[beg:beg + batch], dtype=np.float32)
            count = len(selected)
            pad = (-count) % 128
            if pad:
                selected = np.concatenate(
                    (selected, np.repeat(selected[-1:], pad, axis=0)))
            out = model(torch.from_numpy(selected).cuda())[:count, :7]
            result.append(out.float().cpu().numpy())
    return np.concatenate(result) if result else np.empty((0, 7), np.float32)


def quaternion_angle(a, b):
    """Sign-invariant angle between normalized quaternion updates, in degrees."""
    a, b = a.astype(np.float64), b.astype(np.float64)
    na, nb = np.linalg.norm(a, axis=1), np.linalg.norm(b, axis=1)
    good = (na > 1e-8) & (nb > 1e-8)
    qa, qb = np.zeros_like(a), np.zeros_like(b)
    qa[:, 0] = qb[:, 0] = 1
    qa[good] = a[good] / na[good, None]
    qb[good] = b[good] / nb[good, None]
    dot = np.clip(np.abs(np.einsum("ij,ij->i", qa, qb)), 0, 1)
    return np.rad2deg(2 * np.arccos(dot)).astype(np.float32)


def estimate_sensitivity(model, coords, weights, samples, probes, batch):
    """Approximate first-order squared weight influence on motion outputs."""
    import torch
    samples = min(samples, len(coords))
    if not samples:
        raise ValueError("No active Gaussians for sensitivity analysis")
    selected = np.random.default_rng(114).choice(len(coords), samples, replace=False)
    indices = torch.as_tensor(weights, device="cuda", dtype=torch.long)
    gen = torch.Generator(device="cuda")
    gen.manual_seed(114)
    scores = np.zeros(len(weights), dtype=np.float64)
    steps = 0
    model.train()
    try:
        for beg in range(0, samples, batch):
            xyz = np.ascontiguousarray(coords[selected[beg:beg + batch]], np.float32)
            n = len(xyz)
            pad = (-n) % 128
            if pad:
                xyz = np.concatenate((xyz, np.repeat(xyz[-1:], pad, axis=0)))
            x = torch.from_numpy(xyz).cuda()
            for _ in range(probes):
                model.zero_grad(set_to_none=True)
                y = model(x)[:n, :7].float()
                signs = torch.randint(0, 2, y.shape, device="cuda", dtype=torch.int8,
                                      generator=gen).float().mul_(2).sub_(1)
                loss = (y * signs).sum() / math.sqrt(float(y.numel()))
                loss.backward()
                if model.params.grad is None:
                    raise RuntimeError("tiny-cuda-nn returned no NTC gradients")
                grad = model.params.grad.detach().float()[indices]
                value = model.params.detach().float()[indices]
                scores += (grad * value).square().cpu().numpy()
                steps += 1
        if not np.isfinite(scores).all():
            raise RuntimeError("Nonfinite numerical sensitivity")
    finally:
        model.zero_grad(set_to_none=True)
        model.eval()
    print(f"[SENSITIVITY] {steps} GPU probes across {samples} Gaussians",
          flush=True)
    return scores / steps


def ablation(model, coords, weights, offsets, gids, coeffs,
             requested, limit, batch, destination):
    """Measure motion change from zeroing each selected weight separately."""
    import torch
    summary = []
    with destination.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["weight_id", "gaussian_id", "interpolation_coefficient",
                         "weight_value", "translation_delta_l2", "rotation_angle_deg"])
        for wid in requested:
            row = int(np.searchsorted(weights, wid))
            if row >= len(weights) or int(weights[row]) != wid:
                raise ValueError(f"Weight {wid} is not retained in the HashGrid")
            first, last = int(offsets[row]), int(offsets[row + 1])
            if first == last:
                print(f"[ABLATION] weight={wid}: no in-bounds Gaussian", flush=True)
                continue
            positions = np.linspace(first, last - 1,
                                    min(limit, last - first), dtype=np.int64)
            ids = gids[positions]
            xyz = coords[ids]
            reference = infer(model, xyz, batch)
            original = model.params[wid].detach().clone()
            try:
                # Only the in-memory copy of the model is changed.
                with torch.no_grad():
                    model.params[wid] = 0
                removed = infer(model, xyz, batch)
            finally:
                with torch.no_grad():
                    model.params[wid] = original
            translation = np.linalg.norm(reference[:, :3] - removed[:, :3], axis=1)
            rotation = quaternion_angle(reference[:, 3:7], removed[:, 3:7])
            if not np.isfinite(translation).all() or not np.isfinite(rotation).all():
                raise RuntimeError(f"Nonfinite ablation result for weight {wid}")
            writer.writerows(
                (wid, int(g), float(c), float(original.item()), float(t), float(r))
                for g, c, t, r in zip(ids, coeffs[positions], translation, rotation))
            summary.append({
                "weight_id": int(wid), "structural_gaussians": last - first,
                "measured_gaussians": len(ids),
                "mean_translation_delta_l2": float(np.mean(translation)),
                "max_translation_delta_l2": float(np.max(translation)),
                "mean_rotation_angle_deg": float(np.mean(rotation)),
            })
            print(f"[ABLATION] weight={wid}, Gaussians={len(ids)}, "
                  f"mean translation delta={np.mean(translation):.6g}", flush=True)
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ntc", type=int, default=114)
    p.add_argument("--scene", type=Path, default=paths.COMPRESSED_SCENE_DIR)
    p.add_argument("--wire", type=Path, default=paths.WIRE_DIR)
    p.add_argument("--states", type=Path, default=paths.STATES_DIR)
    p.add_argument("--positions", choices=("state", "initial"), default="state")
    p.add_argument("--out", type=Path, default=paths.HASHGRID_DIR / "individual")
    p.add_argument("--batch", type=int, default=2048)
    p.add_argument("--max-gaussians", type=int, default=0)
    p.add_argument("--cuda-probes", type=int, default=12)
    p.add_argument("--skip-cuda-check", action="store_true")
    p.add_argument("--sensitivity-gaussians", type=int, default=0)
    p.add_argument("--sensitivity-probes", type=int, default=2)
    p.add_argument("--ablate-top", type=int, default=0)
    p.add_argument("--ablate-weights", type=int, nargs="*", default=[])
    p.add_argument("--ablate-limit", type=int, default=256)
    p.add_argument("--inference-batch", type=int, default=512)
    a = p.parse_args()
    if (a.ntc < 0 or a.batch < 16 or a.cuda_probes < 1 or a.ablate_top < 0 or
            a.ablate_limit < 1 or a.sensitivity_gaussians < 0 or
            a.sensitivity_probes < 1 or a.inference_batch < 128 or
            a.inference_batch % 128 or a.max_gaussians < 0):
        p.error("Invalid NTC, batch, probe, or ablation setting")

    import torch
    scene = a.scene.expanduser().resolve()
    checkpoint = a.wire.expanduser().resolve() / f"NTC_{a.ntc:06d}.pth"
    config_path = scene / "NTCs/config.json"
    for src in (checkpoint, config_path):
        if not src.is_file():
            raise FileNotFoundError(src)
    config = json.loads(config_path.read_text())
    layout, features, interp, primes, _ = encoding_layout(config["encoding"])
    wire = torch.load(checkpoint, map_location="cpu", weights_only=True)
    key = "model.params_sparse_int4_block_indices"
    retained = np.asarray(wire[key].cpu().numpy(), dtype=np.int64).reshape(-1)
    total_blocks = (HASH_PARAMS + 9216) // BLOCK
    if (len(retained) != 1556 or len(np.unique(retained)) != len(retained) or
            (retained < 0).any() or (retained >= total_blocks).any()):
        raise ValueError("Expected 1,556 distinct valid sparse INT4 blocks")
    hashed = np.sort(retained[retained < HASH_BLOCKS]).astype(np.int32)
    mlp = np.sort(retained[retained >= HASH_BLOCKS]).astype(np.int32)

    if a.positions == "state":
        state_path = a.states / f"state_{a.ntc:06d}.pt"
        if not state_path.is_file():
            raise FileNotFoundError(
                f"Missing pre-NTC Gaussian state: {state_path}. "
                "Set --states DIR or use --positions initial.")
        state = torch.load(state_path, map_location="cpu", weights_only=True)
        if int(state["timestep"]) != a.ntc:
            raise ValueError("Saved Gaussian state is from another NTC")
        positions = np.asarray(state["xyz"], dtype=np.float32)
    else:
        import util_gau
        positions = np.asarray(
            util_gau.load_ply(str(scene / "init_3dgs.ply")).xyz,
            dtype=np.float32)
    if positions.ndim != 2 or positions.shape[1] != 3 or not np.isfinite(positions).all():
        raise ValueError("Invalid Gaussian XYZ")
    if a.max_gaussians:
        positions = positions[:a.max_gaussians]
    low = np.asarray(wire["xyz_bound_min"], dtype=np.float32).reshape(1, 3)
    high = np.asarray(wire["xyz_bound_max"], dtype=np.float32).reshape(1, 3)
    if np.any(high <= low):
        raise ValueError("Invalid NTC bounds")
    xyz = ((positions - low) / (high - low)).astype(np.float32)
    active = np.logical_and(xyz >= 0, xyz <= 1).all(axis=1)
    print(f"[SCENE] NTC={a.ntc}, positions={a.positions}, "
          f"Gaussians={len(xyz):,}, active={active.sum():,}", flush=True)

    cuda_verified = False
    if not a.skip_cuda_check:
        cuda_check(config["encoding"], xyz, active, layout, features, interp,
                   primes, hashed, a.cuda_probes)
        cuda_verified = True
    weights, offsets, gids, coeffs = make_csr(
        xyz, active, layout, features, interp, primes, hashed, a.batch, progress=True)

    a.out.mkdir(parents=True, exist_ok=True)
    mapping = a.out / f"ntc_{a.ntc:03d}_weight_to_gaussian_{a.positions}.npz"
    np.savez_compressed(
        mapping, weight_ids=weights, offsets=offsets,
        gaussian_ids=gids, interpolation_coefficients=coeffs,
        gaussian_count=np.int32(len(xyz)), ntc_index=np.int32(a.ntc),
        position_source=np.asarray(a.positions),
        mlp_retained_block_ids=mlp, cuda_verified=np.bool_(cuda_verified))
    counts = np.diff(offsets)
    with (a.out / f"ntc_{a.ntc:03d}_weight_counts.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["weight_id", "block_id", "feature", "gaussians"])
        writer.writerows((int(w), int(w // BLOCK), int(w % features), int(n))
                         for w, n in zip(weights, counts))

    ablations = []
    if a.ablate_top or a.ablate_weights or a.sensitivity_gaussians:
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is required for numerical NTC experiments")
        import tinycudann as tcnn
        model = tcnn.NetworkWithInputEncoding(
            n_input_dims=3, n_output_dims=8,
            encoding_config=config["encoding"],
            network_config=config["network"]).cuda().eval()
        full = decode_wire(wire)
        if model.params.numel() != len(full):
            raise ValueError("Decoded NTC parameter count differs from model")
        with torch.no_grad():
            model.params.copy_(torch.from_numpy(full).to(
                device="cuda", dtype=model.params.dtype))
        if a.sensitivity_gaussians:
            scores = estimate_sensitivity(
                model, xyz[active], weights, a.sensitivity_gaussians,
                a.sensitivity_probes, a.inference_batch)
            with (a.out / f"ntc_{a.ntc:03d}_weight_sensitivity.csv").open(
                    "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["weight_id", "first_order_squared_sensitivity"])
                writer.writerows((int(w), float(score))
                                 for w, score in zip(weights, scores))
        if a.ablate_top or a.ablate_weights:
            order = np.argsort(-counts, kind="stable")
            selected_weights = list(map(int, weights[order[:a.ablate_top]]))
            selected_weights += a.ablate_weights
            selected_weights = list(dict.fromkeys(selected_weights))
            ablations = ablation(
                model, xyz, weights, offsets, gids, coeffs,
                selected_weights, a.ablate_limit, a.inference_batch,
                a.out / f"ntc_{a.ntc:03d}_ablations.csv")
    report = {
        "ntc": a.ntc, "position_source": a.positions,
        "gaussians": len(xyz), "gaussians_in_bounds": int(active.sum()),
        "retained_hashgrid_weights": len(weights),
        "retained_mlp_blocks": len(mlp),
        "weight_gaussian_pairs": len(gids),
        "weights_with_gaussians": int(np.count_nonzero(counts)),
        "cuda_index_checks_passed": cuda_verified,
        "sensitivity_gaussians": a.sensitivity_gaussians,
        "sensitivity_probes": a.sensitivity_probes,
        "ablations": ablations,
        "interpretation": ("The indexed weights are direct HashGrid dependencies. "
                           "Interpolation coefficients are not motion changes. "
                           "Ablation measures actual NTC output differences; "
                           "MLP parameters are not localized by this map."),
    }
    (a.out / f"ntc_{a.ntc:03d}_weight_report.json").write_text(
        json.dumps(report, indent=2) + "\n")
    print(f"[SAVED] {mapping}: {len(gids):,} weight-to-Gaussian pairs", flush=True)
    print("[SAFE] Original scene, checkpoints, and viewer unchanged", flush=True)


if __name__ == "__main__":
    main()
