# Ubuntu setup

The viewer requires an NVIDIA GPU, PyTorch with CUDA support, tiny-cuda-nn, and the Gaussian rasterizer. This guide assumes Ubuntu and a compatible NVIDIA driver.

## System packages

```bash
sudo apt update
sudo apt install -y git build-essential cmake ninja-build pkg-config \
  python3-venv libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev \
  freeglut3-dev mesa-utils unzip wget

nvidia-smi
```

## Install Q3DGStream

```bash
git clone https://github.com/publioelon/Q3DGStream.git
cd Q3DGStream
```

On a fresh machine, the installer creates `.venv/` in the repository and builds the CUDA dependencies:

```bash
./scripts/setup_linux_venv.sh
source .venv/bin/activate
```

For Ampere GPUs, select architecture 8.6 before building:

```bash
TCNN_CUDA_ARCHITECTURES=86 TORCH_CUDA_ARCH_LIST=8.6 \
  ./scripts/setup_linux_venv.sh
```

The installer currently uses a CUDA 12.6 PyTorch build. Driver, toolkit, and compiler versions must be compatible with the extensions.

If you have an existing CUDA environment, **reuse it** instead of reinstalling:

```bash
source /path/to/virtualenv/bin/activate
source scripts/env.sh
python3 q3dgstream.py doctor
```

## Example scene

With the Python environment active:

```bash
./scripts/download_flame_steak.sh
```

The example is extracted into `data/scenes/flame_steak/` by default. The expected files include `init_3dgs.ply`, `NTCs/config.json`, and individual `NTC_*.pth` checkpoints.

For data stored on another disk, set `Q3DGSTREAM_SCENE_DIR` and the related variables described in [Configuration](CONFIGURATION.md).

## Run the viewer

The original TCP viewer and sender are documented in [Quickstart](QUICKSTART.md). Both commands run locally and use the Flame Steak scene.

For hybrid NVIDIA laptops using integrated graphics for OpenGL, set PRIME offloading when launching the viewer:

```bash
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia \
  python main.py --tcp_listen 5001 --tcp_bind 127.0.0.1 \
  --tcp_cache "$Q3DGSTREAM_CACHE_DIR/tcp" --tcp_clear_cache \
  --frames 300 --video_fps 30 --autoplay
```

You can inspect the OpenGL device with `glxinfo -B`.

Progressive INT4 and QUIC playback use additional receiver modules and prepared NTC stages. Follow [GPU validation](GPU_VALIDATION.md) after the baseline runs.
