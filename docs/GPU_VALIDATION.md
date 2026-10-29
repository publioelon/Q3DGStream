# GPU validation on Ubuntu

The source unit tests check file formats and syntax. **They do not prove that the CUDA renderer or QUIC playback works.**

## Prerequisites

- An NVIDIA GPU supported by CUDA and the existing `qntcstream` environment.
- `~/qntc_scenes/flame_steak_official` (original Flame Steak scene).
- `/data/3dgs_storage/QNTC-Stream-PQAT-Chunks/qoe_eval/lowbit299_v11_20261011T014600_039285Z/cases/int4_keep05/pqat` (INT4 keep05 PQAT checkpoints).
- `~/snap/firefox/common/QNTC_dynamic_299_priorities_v1/stages` (299 × 4 priority stages).
- `~/snap/firefox/common/QNTC_299_student_states` (saved Gaussian states).

The latter items are external data and intentionally not included in the source repository. For a new machine, create these assets using the research pipeline before running the complete tests.

## Step 1: CUDA model inference and stage integrity

```bash
cd ~/Q3DGStream
source ~/venvs/qntcstream/bin/activate
python scripts/gpu_validation.py --all \
  --viewer ~/Q3DGStream \
  2>&1 | tee ~/snap/firefox/common/Q3DGStream_GPU_validation.log
```

Expected: NTC114 loads and produces finite CUDA results from real Gaussian positions; all NTC114 stage records pass integrity; the 299-frame wire comparison passes; and frames 113 to 115 are evaluated.

`--all` also verifies that the checked-out viewer has local QUIC receiver hooks. Those hooks are not present in the public TCP baseline yet. Do not run the GUI until the local CUDA/QUIC patch is integrated and the static preflight passes.

## Step 2: Actual 30-update QUIC display

In two separate terminals:

```bash
cd ~/Q3DGStream/research/quic/dynamic_priority_adapter
bash run_receiver.sh
```

```bash
cd ~/Q3DGStream/research/quic/dynamic_priority_adapter
bash preflight.sh
QNTC_STAGE_DELAY=0 bash run_sender.sh
```

The receiver clears `/tmp/qntc_dynamic_priority_cache` and requires an existing local TLS certificate, known camera JSON, and patched QUIC renderer. Confirm the scene animates in the viewer, additions are received, no CUDA errors occur, and the colors remain correct. Then evaluate the full 299 updates using `QNTC_END=298`.

Please preserve `/tmp/qntc_dynamic_priority_receiver.log`, `/tmp/qntc_dynamic_priority_sender.log`, and the GPU validation log for diagnosis.
