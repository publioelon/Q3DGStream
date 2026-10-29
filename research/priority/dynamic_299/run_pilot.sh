#!/usr/bin/env bash
set -euo pipefail
Q3DGSTREAM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.. && pwd)"
source "$Q3DGSTREAM_ROOT/scripts/env.sh"
SCRIPT="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT"
python test_offline.py
python prepare_dynamic_saliency.py \
  --out "$Q3DGSTREAM_TIMELINE_FILE"
python rank_ntc_frames.py --start 114 --end 114 --samples-per-tile 128 --probes 2 --emit-stages
python check_schedule.py --start 114 --end 114 --stages
