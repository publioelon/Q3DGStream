# GPU validation

The GitHub tests cover source syntax and the `.qblk` binary format. Real NTC inference and live QUIC playback must also be tested on a machine with an NVIDIA GPU.

Before starting, follow [Configuration](CONFIGURATION.md) to locate the scene, compressed checkpoints, priority stages, and saved Gaussian states. These datasets are not distributed with the source.

## Prepare the checkout

Clone Q3DGStream and activate a working CUDA environment:

```bash
git clone https://github.com/publioelon/Q3DGStream.git
cd Q3DGStream

source /path/to/virtualenv/bin/activate
source scripts/env.sh

python3 q3dgstream.py test
python3 q3dgstream.py doctor
```

If the repository is already installed, run `git pull --ff-only` after checking `git status`. The setup script is not necessary when an existing Python/CUDA environment works.

## Integrate an existing QUIC viewer

The standalone repository includes the TCP viewer and QUIC experiment scripts. To bring in additional GPU-tested viewer modules from another installation, use the source synchronization tool:

```bash
python scripts/sync_gpu_viewer.py --source /path/to/verified-viewer
```

This command only previews the files. If the source has the required receiver and CUDA hooks, copy the selected files into Q3DGStream:

```bash
python scripts/sync_gpu_viewer.py \
  --source /path/to/verified-viewer --apply

git status --short
git diff --stat
```

The source installation is never modified. Earlier destination files are stored in `.local_backups/`. The synchronization tool does not copy checkpoints or TLS keys.

## Validate CUDA inference

With the experimental paths configured, run:

```bash
mkdir -p "$Q3DGSTREAM_LOG_DIR"
python scripts/gpu_validation.py --all --viewer "$PWD" \
  2>&1 | tee "$Q3DGSTREAM_LOG_DIR/gpu_validation.log"
```

The test checks NTC 114 inference on the GPU, its 1,556 retained weight blocks, the local receiver modules, parity of all 299 compressed stage sets, and a three-frame saliency-versus-random reconstruction evaluation.

A successful run reports `RESULT: 5 PASS, 0 FAIL`. This confirms offline inference and stage integrity, not real-time rendered playback.

## Live QUIC pilot

A fixed camera file is required at the viewer root. The QUIC receiver also needs a local test certificate as described in [Configuration](CONFIGURATION.md).

In **terminal 1**:

```bash
source scripts/env.sh
cd research/quic/dynamic_priority_adapter
bash run_receiver.sh
```

In **terminal 2**, from the repository root:

```bash
source scripts/env.sh
cd research/quic/dynamic_priority_adapter
bash preflight.sh
QNTC_STAGE_DELAY=0 bash run_sender.sh
```

The first run transmits 30 NTC updates, 120 priority stage files, and 30 Gaussian additions. Verify the rendered colors and motion, and check the receiver log for errors.

For the complete sequence, stop both processes, start the receiver again, then run:

```bash
QNTC_END=298 QNTC_STAGE_DELAY=0 bash run_sender.sh
```

The log files are written under `"$Q3DGSTREAM_LOG_DIR"` as `dynamic_priority_receiver.log` and `dynamic_priority_sender.log`. Record committed NTC updates per second separately from display FPS.

See [QUIC](QUIC.md) for the transmission protocol and [Results](RESULTS.md) for the current evaluation scope.
