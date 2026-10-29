# GPU validation and QUIC integration (Ubuntu)

The repository's CPU/source tests already run on GitHub Actions. **Real CUDA and QUIC playback must be validated on an NVIDIA GPU.**

## Existing research machine: preserve the working viewer

The current GitHub viewer starts from the earlier TCP baseline. Your locally tested QUIC extensions are in a separate checkout. To avoid overwriting any working code, clone Q3DGStream into a new directory and copy **only a reviewed allowlist** of source files. The process never modifies the original installation.

```bash
cd ~
git clone https://github.com/publioelon/Q3DGStream.git Q3DGStream
source ~/venvs/qntcstream/bin/activate
cd ~/Q3DGStream
python3 q3dgstream.py test
python3 q3dgstream.py doctor
```

If `~/Q3DGStream` already exists and is a Git checkout, use `git -C ~/Q3DGStream pull --ff-only` instead of cloning again.

### Step 1. Preview local GPU/QUIC source synchronization

```bash
cd ~/Q3DGStream
python scripts/sync_gpu_viewer.py --source ~/3DGS-QuaNTiC-Demo
```

The script reports the five required GPU/QUIC source files and optional sender/camera settings. It only **previews** differences. No model weights, private keys, scene assets or experimental caches are copied.

If the preview reports missing `live_quic.py`, `quic_transport.py`, `qntc_progressive_live.py`, QUIC hooks in `main.py`, or priority hooks in `renderer_cuda.py`, **stop and inspect the local checkout**. Do not replace a working file with a guessed version.

### Step 2. Copy only the validated source into Q3DGStream

When the preview is correct:

```bash
python scripts/sync_gpu_viewer.py --source ~/3DGS-QuaNTiC-Demo --apply
git status --short
git diff --stat
```

The source stays unchanged. Older target versions are preserved under `~/Q3DGStream/.local_backups/`, which is excluded from Git. A machine-specific fixed camera file is also excluded.

Review all source diffs and perform the tests below **before committing or pushing** the integrated files.

### Step 3. Real CUDA NTC inference and stage validation

These tests depend on saved research data that are not distributed with the source code:

- `~/qntc_scenes/flame_steak_official`
- `/data/3dgs_storage/QNTC-Stream-PQAT-Chunks/qoe_eval/lowbit299_v11_20261011T014600_039285Z/cases/int4_keep05/pqat`
- `~/snap/firefox/common/QNTC_dynamic_299_priorities_v1/stages`
- `~/snap/firefox/common/QNTC_299_student_states`

```bash
cd ~/Q3DGStream
python scripts/gpu_validation.py --all --viewer ~/Q3DGStream \
  2>&1 | tee ~/snap/firefox/common/Q3DGStream_GPU_validation.log
```

The output should report **5 PASS, 0 FAIL**, including:

1. Loading NTC 114 with 1,991,680 parameters into tiny-cuda-nn and inferring real Gaussian positions on CUDA.
2. Checking all 1,556 unique sparse INT4 blocks from its four `.qblk` stages.
3. Inspecting the integrated local QUIC receiver hooks.
4. Byte-for-byte parity of all 299 staged NTCs against compressed wire checkpoints.
5. Executing saliency versus five random schedules over NTC frames 113 through 115 on CUDA.

Passing this confirms **offline inference and reconstruction**, not end-to-end real-time playback.

### Step 4. Run the 30-update real QUIC pilot

Open two terminals, each with `source ~/venvs/qntcstream/bin/activate`. The receiver requires `camera_flame_steak.json` and a local TLS certificate/key in `/tmp/qntc_progressive.{crt,key}`. Do not publish these key files.

**Terminal A, receiver**:

```bash
cd ~/Q3DGStream/research/quic/dynamic_priority_adapter
bash run_receiver.sh
```

**Terminal B, sender**:

```bash
cd ~/Q3DGStream/research/quic/dynamic_priority_adapter
bash preflight.sh
QNTC_STAGE_DELAY=0 bash run_sender.sh
```

Confirm normal Gaussian colors and motion, that 30 additions and 120 priority stages arrive, and that no CUDA errors appear.

The receiver clears *only* the dedicated `/tmp/qntc_dynamic_priority_cache`; it does not change the original scene or model.

### Step 5. Full 299-update QUIC sequence

After the 30-update pilot succeeds, close the receiver and sender. Relaunch the receiver and then run:

```bash
cd ~/Q3DGStream/research/quic/dynamic_priority_adapter
QNTC_END=298 QNTC_STAGE_DELAY=0 bash run_sender.sh
```

Check actual committed NTC update rate and playback behavior. Viewer render FPS alone does not establish 30 NTC transformations/s.

## Logs to preserve

```text
~/snap/firefox/common/Q3DGStream_GPU_validation.log
/tmp/qntc_dynamic_priority_receiver.log
/tmp/qntc_dynamic_priority_sender.log
```

GPU performance, progressive rendering quality and adaptive network scheduling require the corresponding hardware and network experiments before being claimed as validated.
