#!/usr/bin/env python3
"""Inspect which Gaussians access one retained HashGrid weight."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import q3dg_paths as paths


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("weight_id", type=int, help="Absolute index in the NTC parameter vector")
    p.add_argument("--ntc", type=int, default=114)
    p.add_argument("--positions", choices=("state", "initial"), default="state")
    p.add_argument("--map", type=Path, default=None)
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--export", type=Path, default=None,
                   help="Optional CSV with all matching Gaussian IDs and coefficients")
    a = p.parse_args()
    if a.limit < 0:
        p.error("--limit must not be negative")
    mapping = a.map or (paths.HASHGRID_DIR / "individual" /
                        f"ntc_{a.ntc:03d}_weight_to_gaussian_{a.positions}.npz")
    if not mapping.is_file():
        raise FileNotFoundError(mapping)
    with np.load(mapping, allow_pickle=False) as data:
        weights = data["weight_ids"]
        offsets = data["offsets"]
        row = int(np.searchsorted(weights, a.weight_id))
        if row >= len(weights) or int(weights[row]) != a.weight_id:
            raise ValueError(f"Weight {a.weight_id} is not a retained HashGrid weight")
        beg, end = int(offsets[row]), int(offsets[row + 1])
        gids = data["gaussian_ids"][beg:end]
        coefficients = data["interpolation_coefficients"][beg:end]
        print(f"NTC: {int(data['ntc_index'])}")
        print(f"Position source: {str(data['position_source'])}")
        print(f"Weight index: {a.weight_id} (block {a.weight_id // 64})")
        print(f"Gaussians structurally accessing this weight: {len(gids):,}")
        print(f"CUDA index checks: {'passed' if bool(data['cuda_verified']) else 'not run'}")
        for gid, coeff in zip(gids[:a.limit], coefficients[:a.limit]):
            print(f"  Gaussian {int(gid):>7}  coefficient={float(coeff):.8g}")
        if a.export:
            a.export.parent.mkdir(parents=True, exist_ok=True)
            with a.export.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(("weight_id", "gaussian_id", "interpolation_coefficient"))
                writer.writerows((a.weight_id, int(g), float(c))
                                 for g, c in zip(gids, coefficients))
            print(f"Saved {len(gids):,} relationships to {a.export}")


if __name__ == "__main__":
    main()
