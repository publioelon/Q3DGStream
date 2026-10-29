#!/usr/bin/env bash
set -euo pipefail
Q3DGSTREAM_ROOT="${Q3DGSTREAM_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
source "$Q3DGSTREAM_ROOT/scripts/env.sh"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$Q3DGSTREAM_ROOT"
mkdir -p "$Q3DGSTREAM_CACHE_DIR"
# Only check inputs and available cache space.
python "$DIR/send_dynamic_priority.py" --start 0 --end "${QNTC_END:-29}" --preflight-only
