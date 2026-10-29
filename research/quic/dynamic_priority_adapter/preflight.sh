#!/usr/bin/env bash
set -euo pipefail
Q3DGSTREAM_ROOT="${Q3DGSTREAM_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
source "$HOME/venvs/qntcstream/bin/activate"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$Q3DGSTREAM_ROOT"
python "$DIR/send_dynamic_priority.py" --start 0 --end "${QNTC_END:-29}" --preflight-only
