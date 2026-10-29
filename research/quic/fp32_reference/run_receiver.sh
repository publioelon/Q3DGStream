#!/usr/bin/env bash
set -euo pipefail
Q3DGSTREAM_ROOT="${Q3DGSTREAM_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
source "$Q3DGSTREAM_ROOT/scripts/env.sh"
VIEWER="${QNTC_VIEWER:-$Q3DGSTREAM_ROOT}"
CACHE="${QNTC_FP32_CACHE:-$Q3DGSTREAM_CACHE_DIR/qntc_fp32_reference_cache}"
# Fail closed: this command uses --quic_clear_cache, which deletes the cache dir.
[[ "$(basename "$CACHE")" == 'qntc_fp32_reference_cache' ]] || {
  echo '[STOP] For safety, cache must be a dedicated folder named qntc_fp32_reference_cache' >&2
  exit 1
}
[[ "$CACHE" != "$VIEWER" && "$CACHE" != "$Q3DGSTREAM_SCENE_DIR" && "$CACHE" != "$Q3DGSTREAM_SCENE_DIR"/* ]] || {
  echo '[STOP] Cache must be outside the source scene' >&2
  exit 1
}
mkdir -p "$Q3DGSTREAM_CACHE_DIR" "$Q3DGSTREAM_LOG_DIR"
cd "$VIEWER"
[[ -f camera_flame_steak.json ]] || { echo '[STOP] missing reference camera JSON' >&2; exit 1; }
[[ -f renderer_cuda.py ]] || { echo '[STOP] missing renderer' >&2; exit 1; }
# Preserve the working code only if no backups exist. Never overwrite earlier backups.
[[ -f renderer_cuda.py.WORKING_BACKUP ]] || cp -a renderer_cuda.py renderer_cuda.py.WORKING_BACKUP
[[ -f main.py.WORKING_BACKUP ]] || cp -a main.py main.py.WORKING_BACKUP
# Local-only test certificate. Require it to exist to avoid surprising prompts.
CERT="$Q3DGSTREAM_TLS_CERT"
KEY="$Q3DGSTREAM_TLS_KEY"
[[ -s "$CERT" && -s "$KEY" ]] || { echo '[STOP] Missing local QUIC cert/key, see README' >&2; exit 1; }
echo '[RECEIVER] Native QUIC (NOT progressive sidecar), original FP32 NTCs and additions'
echo "[RECEIVER] Cache: $CACHE"
# The exact bounds come from NTC_000000, sent before config.json.
env -u STATE_SYNC_INTERVAL -u QNTC_PROGRESSIVE_QUIC -u QNTC_STATIC_CPU_PROBE \
  LOCK_CAMERA=1 FIXED_CAMERA_JSON="$VIEWER/camera_flame_steak.json" \
  NTC_TRANSLATION_SCALE=1.0 NTC_ROTATION_MODE=current \
  USE_NTC_MASK=0 LOOP_PLAYBACK=0 QNTC_PRIORITY_VIS=0 \
  NTC_DEBUG=0 NTC_DEBUG_DXYZ=0 \
  python -u main.py --quic_listen 5003 --quic_bind 127.0.0.1 \
  --quic_cache "$CACHE" --quic_clear_cache \
  --quic_cert "$CERT" --quic_key "$KEY" \
  --frames 300 --autoplay --video_fps 30 \
  2>&1 | tee "$Q3DGSTREAM_LOG_DIR/fp32_reference_receiver.log"
