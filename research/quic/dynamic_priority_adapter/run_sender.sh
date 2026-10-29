#!/usr/bin/env bash
set -euo pipefail
Q3DGSTREAM_ROOT="${Q3DGSTREAM_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
source "$Q3DGSTREAM_ROOT/scripts/env.sh"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$Q3DGSTREAM_ROOT" # allow import of project's existing quic_transport
mkdir -p "$Q3DGSTREAM_LOG_DIR"
python -u "$DIR/send_dynamic_priority.py" \
  --start 0 --end "${QNTC_END:-29}" \
  --stage-delay "${QNTC_STAGE_DELAY:-0}" \
  --warmup-delay "${QNTC_WARMUP_DELAY:-2}" "$@" \
  2>&1 | tee "$Q3DGSTREAM_LOG_DIR/dynamic_priority_sender.log"
