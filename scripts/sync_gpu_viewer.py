#!/usr/bin/env python3
"""Preview or safely copy locally validated QUIC viewer source into Q3DGStream.

The source installation is read-only. --apply changes only the target checkout,
backing up overwritten files under target/.local_backups (ignored by Git).
Weights, 3D scenes, saved states, and TLS secrets are never copied.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

REQUIRED = ("main.py", "renderer_cuda.py", "live_quic.py",
            "quic_transport.py", "qntc_progressive_live.py")
OPTIONAL = ("qntc_progressive_send.py", "camera_flame_steak.json")
SOURCE_MARKERS = {
    "main.py": ("quic_listen",),
    "qntc_progressive_live.py": ("decode_stages", "part_versions"),
    "renderer_cuda.py": ("qntc_priority_vis",),
}

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for part in iter(lambda: source.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()

def safe_file(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Not a safe regular file: {path}")
    if path.stat().st_size > 2_000_000:
        raise ValueError(f"Unusually large source file: {path}")

def plan(source: Path, target: Path) -> list[dict]:
    if not source.is_dir() or not target.is_dir():
        raise ValueError("Both source and target must be existing directories")
    s, t = source.resolve(), target.resolve()
    if s == t or s in t.parents or t in s.parents:
        raise ValueError("Source and target must be separate, non-nested directories")
    for name in ("README.md", "q3dgstream.py", ".git"):
        if not (target / name).exists():
            raise ValueError(f"Target is not a Q3DGStream Git checkout: missing {name}")
    entries, missing = [], []
    for name in REQUIRED + OPTIONAL:
        src = source / name
        if not src.exists() and not src.is_symlink():
            if name in REQUIRED:
                missing.append(name)
            continue
        safe_file(src)
        if name in SOURCE_MARKERS:
            content = src.read_text(encoding="utf-8", errors="replace")
            for marker in SOURCE_MARKERS[name]:
                if marker not in content:
                    raise ValueError(f"Required receiver hook {marker!r} missing: {src}")
        dst = target / name
        if dst.is_symlink() or (dst.exists() and not dst.is_file()):
            raise ValueError(f"Unsafe destination: {dst}")
        new = digest(src)
        old = digest(dst) if dst.is_file() else None
        entries.append({"name": name, "source_sha256": new,
                        "target_sha256": old, "size_bytes": src.stat().st_size,
                        "action": "unchanged" if new == old else
                                  "replace" if old else "add"})
    if missing:
        raise ValueError("Missing local QUIC source: " + ", ".join(missing))
    return entries

def apply(source: Path, target: Path, entries: list[dict]) -> Path | None:
    changed = [row for row in entries if row["action"] != "unchanged"]
    if not changed:
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = target / ".local_backups" / f"gpu_viewer_{stamp}_{os.getpid()}"
    backup.mkdir(parents=True, exist_ok=False)
    for row in changed:
        src, dst = source / row["name"], target / row["name"]
        safe_file(src)
        if digest(src) != row["source_sha256"]:
            raise RuntimeError(f"Source changed since preview: {src}")
        if dst.exists():
            if dst.is_symlink() or digest(dst) != row["target_sha256"]:
                raise RuntimeError(f"Target changed since preview: {dst}")
            shutil.copy2(dst, backup / row["name"])
    (backup / "manifest.json").write_text(
        json.dumps({"source": str(source), "target": str(target),
                    "files": changed}, indent=2) + "\n")
    for row in changed:
        src, dst = source / row["name"], target / row["name"]
        with tempfile.NamedTemporaryFile(dir=target, prefix=".q3dg_sync_",
                                         delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            shutil.copy2(src, tmp_path)
            os.replace(tmp_path, dst)
        finally:
            tmp_path.unlink(missing_ok=True)
    return backup

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path.home() / "3DGS-QuaNTiC-Demo")
    p.add_argument("--target", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--apply", action="store_true", help="Actually copy files into Q3DGStream")
    a = p.parse_args()
    try:
        entries = plan(a.source, a.target)
        print("Q3DGStream | local QUIC source integration")
        print("Source (READ ONLY):", a.source, "\nTarget:", a.target)
        for row in entries:
            print(f"  {row['action']:9} {row['name']:28} {row['size_bytes']:>8} bytes")
        if not a.apply:
            print("\nDRY RUN. Re-run with --apply after reviewing the file list.")
            return 0
        backup = apply(a.source, a.target, entries)
        print("\nCopied. Previous target versions saved at:", backup or "none")
        print("Next: python scripts/gpu_validation.py --all --viewer .")
        print("Review changes with git diff before publishing them.")
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f"[STOP] {error}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
