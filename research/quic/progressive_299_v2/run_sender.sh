#!/usr/bin/env bash
set -euo pipefail
Q3DGSTREAM_ROOT="${Q3DGSTREAM_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
source "$Q3DGSTREAM_ROOT/scripts/env.sh"
cd "$Q3DGSTREAM_ROOT"
mkdir -p "$Q3DGSTREAM_LOG_DIR"
STAGE_DELAY="${QNTC_STAGE_DELAY:-0.045}"
echo "[QUIC] 299 compressed NTC updates, stage-delay=${STAGE_DELAY}s"
mkdir -p "$Q3DGSTREAM_LOG_DIR"
python -u qntc_progressive_send.py \
  --host 127.0.0.1 --port 5002 --insecure \
  --start 0 --end 298 --order saliency \
  --warmup-delay 2 --stage-delay "$STAGE_DELAY" \
  2>&1 | tee "$Q3DGSTREAM_LOG_DIR/progressive_sender_v2.log"
