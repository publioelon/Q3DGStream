#!/usr/bin/env bash
set -euo pipefail
Q3DGSTREAM_ROOT="${Q3DGSTREAM_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
source "$Q3DGSTREAM_ROOT/scripts/env.sh"
VIEWER="$Q3DGSTREAM_ROOT"
CACHE="$Q3DGSTREAM_CACHE_DIR/qntc_dynamic_priority_cache"
[[ ! -L "$CACHE" ]] || { echo '[STOP] Cache path is a symlink' >&2; exit 1; }
[[ -s "$Q3DGSTREAM_TLS_CERT" && -s "$Q3DGSTREAM_TLS_KEY" ]] || {
  echo '[STOP] Missing local QUIC certificate/key; see docs/GPU_VALIDATION.md' >&2; exit 1;
}
[[ -f "$VIEWER/camera_flame_steak.json" ]] || { echo '[STOP] Missing fixed camera' >&2; exit 1; }
[[ -f "$VIEWER/qntc_progressive_live.py" ]] || { echo '[STOP] Missing progressive receiver sidecar' >&2; exit 1; }
# A new Q3DGStream checkout keeps backups under .local_backups/ during safe synchronization.
mkdir -p "$Q3DGSTREAM_CACHE_DIR" "$Q3DGSTREAM_LOG_DIR"
cd "$VIEWER"
python - <<'PY'
from pathlib import Path
s=Path('renderer_cuda.py').read_text()
if 'if self.qntc_priority_vis:' not in s or 'sh_vis = rendered_gaussians.sh' not in s:
    raise SystemExit('[STOP] Working original-SH color bypass not detected; do not run')
q=Path('qntc_progressive_live.py').read_text()
if 'part_versions' not in q or 'decode_stages' not in q:
    raise SystemExit('[STOP] Expected bounded progressive v2 receiver not installed')
print('[OK] Working renderer color fix and bounded progressive receiver detected')
PY
# Only the dedicated priority cache is cleared.
echo '[RECEIVER] Dynamic priority QUIC pilot on UDP 5002; local-only'
env -u STATE_SYNC_INTERVAL -u QNTC_STATIC_CPU_PROBE \
    LOCK_CAMERA=1 FIXED_CAMERA_JSON="$VIEWER/camera_flame_steak.json" \
    NTC_TRANSLATION_SCALE=1.0 NTC_ROTATION_MODE=current \
    USE_NTC_MASK=0 QNTC_PRIORITY_VIS=0 QNTC_PROGRESSIVE_QUIC=1 \
    LOOP_PLAYBACK=1 QNTC_PROGRESSIVE_CPU_CACHE=10 \
    NTC_DEBUG=0 NTC_DEBUG_DXYZ=0 \
    python -u main.py --quic_listen 5002 --quic_bind 127.0.0.1 \
      --quic_cache "$CACHE" --quic_clear_cache \
      --quic_cert "$Q3DGSTREAM_TLS_CERT" --quic_key "$Q3DGSTREAM_TLS_KEY" \
      --frames 300 --autoplay --video_fps 30 2>&1 | tee "$Q3DGSTREAM_LOG_DIR/dynamic_priority_receiver.log"
