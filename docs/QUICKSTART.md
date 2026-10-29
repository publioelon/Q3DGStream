# Quickstart

The repository can be explored without a GPU. Rendering and NTC inference require the CUDA setup described in [Ubuntu installation](linux.md).

## Clone and run the checks

```bash
git clone https://github.com/publioelon/Q3DGStream.git
cd Q3DGStream
python3 q3dgstream.py demo
python3 q3dgstream.py test
python3 q3dgstream.py doctor
```

`demo` constructs one synthetic INT4 priority stage and parses it. `test` runs the Python source and format tests. `doctor` checks the local dependencies and looks for the example scene and the QUIC receiver.

## Set up the viewer

On Ubuntu with an NVIDIA GPU, follow [the installation guide](linux.md) to install or activate the `qntcstream` environment, compile the CUDA extensions, and obtain the Flame Steak scene.

For an existing environment:

```bash
source ~/venvs/qntcstream/bin/activate
cd ~/Q3DGStream
python3 q3dgstream.py doctor
```

Run the baseline TCP viewer and sender in **separate terminals**.

**Viewer**

```bash
cd ~/Q3DGStream
python main.py --tcp_listen 5001 --tcp_bind 127.0.0.1 \
  --tcp_cache /tmp/q3dgstream_tcp --tcp_clear_cache \
  --frames 300 --video_fps 30 --autoplay
```

**Sender**

```bash
cd ~/Q3DGStream
python tcp_fvv_sender.py --host 127.0.0.1 --port 5001 \
  --root "$HOME/qntc_scenes/flame_steak_official" \
  --start 0 --end 298 --ntc_stride 1 --no_additions
```

This exercises the original TCP playback path. It does not transmit the saliency-ranked INT4 stages.

## Inspect a real NTC stage

After generating the priority schedules, use the inspector on any `.qblk` file:

```bash
python3 q3dgstream.py inspect-stage \
  "$HOME/snap/firefox/common/QNTC_dynamic_299_priorities_v1/stages/NTC_000114_P0.qblk"
```

The inspector reports the NTC index, priority stage, and number of weight records. Details of the binary layout are in [Formats](FORMATS.md).

For the CUDA experiments, see [GPU validation](GPU_VALIDATION.md). For the progressive sender and receiver, see [QUIC streaming](QUIC.md). The original datasets and trained checkpoints are required to reproduce the measurements in [Experiments](EXPERIMENTS.md).
