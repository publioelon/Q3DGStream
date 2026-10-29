#!/usr/bin/env bash
set -euo pipefail
Q3DGSTREAM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.. && pwd)"
source "$Q3DGSTREAM_ROOT/scripts/env.sh"
cd "$(dirname "$0")"
python map_gaussian_blocks.py --ntc 114 --batch-size 2048 --cuda-probes 12 "$@"
