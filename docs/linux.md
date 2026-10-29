# Ubuntu installation

Q3DGStream's rendering path requires an NVIDIA GPU, CUDA, PyTorch, tiny-cuda-nn, and the Gaussian rasterizer used by 3D Gaussian Splatting. The following commands are for Ubuntu. If the dependencies are already installed and working, skip the environment creation and use the existing virtual environment.

## System packages

```bash
sudo apt update
sudo apt install -y git build-essential cmake ninja-build pkg-config \
    python3-venv libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev \
    freeglut3-dev mesa-utils unzip wget
```

Check that the NVIDIA driver is available:

```bash
nvidia-smi
```

The CUDA driver, toolkit, and PyTorch build must be compatible. Installing the Python dependencies does not install or repair the system's NVIDIA driver.

## Clone the source

```bash
cd ~
git clone https://github.com/publioelon/Q3DGStream.git
cd Q3DGStream
```

If the repository is already checked out, use `git pull --ff-only` to update it.

## Python and CUDA dependencies

The setup script creates `~/venvs/qntcstream`, installs the project's PyTorch build, and compiles the CUDA extensions. **Do not rerun it over a working environment unless you intend to change the installed dependencies.**

For an RTX 40-series GPU (Ada):

```bash
./scripts/setup_linux_venv.sh
source ~/venvs/qntcstream/bin/activate
```

For an RTX 30-series GPU (Ampere):

```bash
TCNN_CUDA_ARCHITECTURES=86 TORCH_CUDA_ARCH_LIST=8.6 \
    ./scripts/setup_linux_venv.sh
source ~/venvs/qntcstream/bin/activate
```

To use an existing environment instead:

```bash
source ~/venvs/qntcstream/bin/activate
python q3dgstream.py doctor
```

The setup script currently installs a CUDA 12.6 PyTorch build and compiles tiny-cuda-nn and the rasterizer from source. CUDA extensions can be sensitive to driver, compiler, and toolkit versions.

## Example scene

```bash
cd ~/Q3DGStream
./scripts/download_flame_steak.sh
```

The downloader places the Flame Steak scene in `~/qntc_scenes/flame_steak_official/`. The directory should contain the initial Gaussian scene (`init_3dgs.ply`), NTC configuration, and per-frame NTC checkpoints.

## TCP playback

The original viewer is retained as a baseline. Run it in two terminals with the virtual environment active.

**Terminal 1: viewer**

```bash
cd ~/Q3DGStream
source ~/venvs/qntcstream/bin/activate
python main.py --tcp_listen 5001 --tcp_bind 127.0.0.1 \
  --tcp_cache /tmp/q3dgstream_tcp --tcp_clear_cache \
  --frames 300 --video_fps 30 --autoplay
```

**Terminal 2: sender**

```bash
cd ~/Q3DGStream
source ~/venvs/qntcstream/bin/activate
python tcp_fvv_sender.py --host 127.0.0.1 --port 5001 \
  --root "$HOME/qntc_scenes/flame_steak_official" \
  --start 0 --end 298 --ntc_stride 1 --no_additions
```

The `--no_additions` option follows the existing baseline demonstration; it is not equivalent to the full dynamic scene with per-frame Gaussian additions.

## Hybrid NVIDIA laptops

On laptops that launch OpenGL applications on the integrated GPU, the following environment variables select NVIDIA PRIME offloading:

```bash
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia \
  python main.py --tcp_listen 5001 --tcp_bind 127.0.0.1 \
  --tcp_cache /tmp/q3dgstream_tcp --tcp_clear_cache \
  --frames 300 --video_fps 30 --autoplay
```

The OpenGL renderer can be checked with `glxinfo -B`. CUDA and OpenGL device selection are related but separate concerns.

## Progressive QUIC

The QUIC experiments need additional receiver modules and precomputed compressed NTC stages. They are not enabled by the TCP commands above. Follow the [GPU validation and integration guide](GPU_VALIDATION.md) and [QUIC notes](QUIC.md) before launching the progressive sender.

The project also uses `antialiasing=False` in the Linux rasterizer settings. Older rasterizer builds may not accept unsupported configuration fields; use the versions installed by the project's setup script or an already verified environment.
