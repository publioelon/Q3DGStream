"""Shared filesystem locations for Q3DGStream experiments.

Paths can be set through environment variables. Generated data is kept
outside version-controlled source files by default.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def configured(name: str, default: Path) -> Path:
    """Return an environment override or the project default."""
    return Path(os.environ.get(name, str(default))).expanduser()


DATA_DIR = configured("Q3DGSTREAM_DATA_DIR", ROOT / "data")
SCENE_DIR = configured("Q3DGSTREAM_SCENE_DIR", DATA_DIR / "scenes" / "flame_steak")
EXPERIMENT_DIR = configured("Q3DGSTREAM_EXPERIMENT_DIR", DATA_DIR / "experiments" / "int4_keep05")
COMPRESSED_SCENE_DIR = configured("Q3DGSTREAM_COMPRESSED_SCENE_DIR", EXPERIMENT_DIR / "scenes" / "candidate")
WIRE_DIR = configured("Q3DGSTREAM_WIRE_DIR", EXPERIMENT_DIR / "wire")
RUNTIME_DIR = configured("Q3DGSTREAM_RUNTIME_DIR", EXPERIMENT_DIR / "runtime")
PRIORITIES_DIR = configured("Q3DGSTREAM_PRIORITIES_DIR", DATA_DIR / "priorities")
STAGES_DIR = configured("Q3DGSTREAM_STAGES_DIR", PRIORITIES_DIR / "stages")
STATES_DIR = configured("Q3DGSTREAM_STATES_DIR", DATA_DIR / "states")
SALIENCY_DIR = configured("Q3DGSTREAM_SALIENCY_DIR", DATA_DIR / "saliency" / "raw")
TIMELINE_FILE = configured("Q3DGSTREAM_TIMELINE_FILE", DATA_DIR / "saliency" / "timeline.json")
AUDIT_DIR = configured("Q3DGSTREAM_AUDIT_DIR", DATA_DIR / "audits")
HASHGRID_DIR = configured("Q3DGSTREAM_HASHGRID_DIR", DATA_DIR / "hashgrid")
HASHGRID_MAP = configured("Q3DGSTREAM_HASHGRID_MAP", HASHGRID_DIR / "ntc_114_hash_block_to_gaussian_ids.npz")
TILE_SUPPORT_FILE = configured("Q3DGSTREAM_TILE_SUPPORT_FILE", AUDIT_DIR / "tile_block_dependencies_114.json")
OUTPUT_DIR = configured("Q3DGSTREAM_OUTPUT_DIR", DATA_DIR / "outputs")
CACHE_DIR = configured("Q3DGSTREAM_CACHE_DIR", DATA_DIR / "cache")
LOG_DIR = configured("Q3DGSTREAM_LOG_DIR", DATA_DIR / "logs")
TLS_CERT = configured("Q3DGSTREAM_TLS_CERT", DATA_DIR / "local" / "localhost.crt")
TLS_KEY = configured("Q3DGSTREAM_TLS_KEY", DATA_DIR / "local" / "localhost.key")
