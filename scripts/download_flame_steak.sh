#!/usr/bin/env bash
set -e

Q3DGSTREAM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$Q3DGSTREAM_ROOT/scripts/env.sh"
SCENE_DIR="$(dirname "$Q3DGSTREAM_SCENE_DIR")"
SCENE_ZIP="${SCENE_DIR}/flame_steak.zip"
OUT_DIR="$Q3DGSTREAM_SCENE_DIR"

mkdir -p "$SCENE_DIR"
cd "$SCENE_DIR"

python -m pip install gdown

if [ ! -f "$SCENE_ZIP" ]; then
  echo "[Q3DGStream] Downloading Flame Steak scene..."
  gdown 1AXDqSzSaT_uNu_DhKeSmZmrBAfuOhWYY -O "$SCENE_ZIP"
else
  echo "[QNTC] Zip already exists: $SCENE_ZIP"
fi

if [ ! -d "$OUT_DIR" ]; then
  echo "[QNTC] Extracting scene..."
  unzip "$SCENE_ZIP" -d "$OUT_DIR"
else
  echo "[QNTC] Scene already extracted: $OUT_DIR"
fi

echo ""
echo "[QNTC] Scene ready at: $OUT_DIR"
echo "[QNTC] Checking files:"
ls -lh "$OUT_DIR/init_3dgs.ply"
ls -lh "$OUT_DIR/NTCs/config.json"
echo "[QNTC] NTC count:"
ls "$OUT_DIR"/NTCs/NTC_*.pth | wc -l
