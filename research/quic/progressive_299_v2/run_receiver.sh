#!/usr/bin/env bash
set -euo pipefail
Q3DGSTREAM_ROOT="${Q3DGSTREAM_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
source "$Q3DGSTREAM_ROOT/scripts/env.sh"
mkdir -p "$Q3DGSTREAM_CACHE_DIR" "$Q3DGSTREAM_LOG_DIR"
cd "$Q3DGSTREAM_ROOT"
if [[ ! -s "$Q3DGSTREAM_TLS_CERT" || ! -s "$Q3DGSTREAM_TLS_KEY" ]]; then
  echo '[STOP] QUIC local certificate missing. Follow README to create it.' >&2
  exit 1
fi
echo '[QUIC] Viewer: original colors, 300 display frames, no loop, CPU decode off UI thread'
LOOP_PLAYBACK=0 QNTC_PRIORITY_VIS=0 QNTC_PROGRESSIVE_QUIC=1 \
NTC_DEBUG=0 NTC_DEBUG_DXYZ=0 QNTC_PROGRESSIVE_CPU_CACHE=10 \
python -u main.py \
  --quic_listen 5002 \
  --quic_bind 127.0.0.1 \
  --quic_cache "$Q3DGSTREAM_CACHE_DIR/qntc_progressive_cache" \
  --quic_clear_cache \
  --quic_cert "$Q3DGSTREAM_TLS_CERT" \
  --quic_key "$Q3DGSTREAM_TLS_KEY" \
  --frames 300 --autoplay --video_fps 30 \
  2>&1 | tee "$Q3DGSTREAM_LOG_DIR/progressive_receiver_v2.log"
