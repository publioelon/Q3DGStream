#!/usr/bin/env bash
set -euo pipefail
Q3DGSTREAM_ROOT="${Q3DGSTREAM_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
source "$Q3DGSTREAM_ROOT/scripts/env.sh"
VIEWER="${QNTC_VIEWER:-$Q3DGSTREAM_ROOT}"
CACHE="${QNTC_FP32_CACHE:-$Q3DGSTREAM_CACHE_DIR/qntc_fp32_reference_cache}"
HERE="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$VIEWER${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p "$Q3DGSTREAM_LOG_DIR"
python -u "$HERE/fp32_quic_sender.py" --cache "$CACHE" "$@" \
  2>&1 | tee "$Q3DGSTREAM_LOG_DIR/fp32_reference_sender.log"
