# GPU validation

The GitHub tests cover parsing, serialization, and source-level checks. Actual NTC inference and progressive rendering require an NVIDIA GPU with the CUDA dependencies installed.

The instructions below use an existing Ubuntu installation of the original viewer to bring its locally tested QUIC modules into a **separate Q3DGStream checkout**. The source installation is read-only throughout this procedure.

## Prepare the Q3DGStream checkout

```bash
cd ~
git clone https://github.com/publioelon/Q3DGStream.git
cd Q3DGStream
source ~/venvs/qntcstream/bin/activate

python3 q3dgstream.py test
python3 q3dgstream.py doctor
```

If `~/Q3DGStream` already exists, update it with `git -C ~/Q3DGStream pull --ff-only` rather than cloning again. Reuse a working `qntcstream` environment; rebuilding CUDA extensions is unnecessary for these tests.

## Bring in the locally tested QUIC receiver

First preview the source files:

```bash
cd ~/Q3DGStream
python scripts/sync_gpu_viewer.py --source ~/3DGS-QuaNTiC-Demo
```

The source path above is an example from the reference Ubuntu setup. Use `--source /path/to/working/viewer` on another machine. The tool checks required QUIC receiver modules and reports the files it would add or replace without writing anything.

After confirming that the preview identifies the expected source:

```bash
python scripts/sync_gpu_viewer.py \
  --source ~/3DGS-QuaNTiC-Demo --apply

git status --short
git diff --stat
```

The integration script copies a small allowlist of viewer and transport files, leaving the source directory unchanged. Previous destination versions are backed up in `.local_backups/`. Scene models, private keys, experimental states, and TLS certificates are not copied.

Review the changes before committing them.

## Offline CUDA tests

The full validation uses these previously generated inputs:

- Flame Steak: `~/qntc_scenes/flame_steak_official/`
- INT4 keep05 PQAT run: `/data/3dgs_storage/QNTC-Stream-PQAT-Chunks/qoe_eval/lowbit299_v11_20261011T014600_039285Z/cases/int4_keep05/pqat/`
- Priority stages: `~/snap/firefox/common/QNTC_dynamic_299_priorities_v1/stages/`
- Saved Gaussian states: `~/snap/firefox/common/QNTC_299_student_states/`

These paths reflect the original experiment. The saved checkpoints and states are not included in the repository.

```bash
cd ~/Q3DGStream
python scripts/gpu_validation.py --all --viewer ~/Q3DGStream \
  2>&1 | tee ~/snap/firefox/common/Q3DGStream_GPU_validation.log
```

The script runs five checks:

1. Load the INT4 keep05 runtime NTC 114 and evaluate 1,024 active Gaussian positions with tiny-cuda-nn on CUDA.
2. Verify the 1,556 indexed weight records in NTC 114's four priority files.
3. Check the integrated QUIC receiver modules.
4. Compare all 299 stage sets against their compressed wire checkpoints.
5. Evaluate saliency ordering against five random orders on frames 113 through 115.

A successful run ends in `RESULT: 5 PASS, 0 FAIL`. This is an **offline CUDA and source-integrity check**; it does not measure rendered frames per second.

## Live QUIC test

The viewer needs a fixed-camera file and a local QUIC certificate/key at `/tmp/qntc_progressive.crt` and `/tmp/qntc_progressive.key`. Keep the private key out of Git.

Launch the receiver and sender in different terminals.

**Receiver**

```bash
cd ~/Q3DGStream/research/quic/dynamic_priority_adapter
bash run_receiver.sh
```

**Sender**

```bash
cd ~/Q3DGStream/research/quic/dynamic_priority_adapter
bash preflight.sh
QNTC_STAGE_DELAY=0 bash run_sender.sh
```

The first test streams 30 animation updates, with 120 stage files and 30 Gaussian additions. Check the rendered colors and motion as well as the terminal logs. The receiver clears only its dedicated cache at `/tmp/qntc_dynamic_priority_cache`.

For the 299-update sequence, close the sender and receiver, restart the receiver, then run:

```bash
QNTC_END=298 QNTC_STAGE_DELAY=0 bash run_sender.sh
```

Record actual applied NTC updates per second separately from the viewer's display FPS.

## Logs

The validation script and live sender/receiver produce:

```text
~/snap/firefox/common/Q3DGStream_GPU_validation.log
/tmp/qntc_dynamic_priority_receiver.log
/tmp/qntc_dynamic_priority_sender.log
```

Use those logs to investigate missing stages, receiver errors, or CUDA exceptions before changing the installation. See [QUIC](QUIC.md) for details of the progressive state update.
