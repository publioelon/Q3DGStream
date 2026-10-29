# Q3DGStream

### Saliency-Driven Adaptive Streaming of Dynamic 3D Gaussian Splatting over QUIC

Q3DGStream explores progressive transmission of dynamic 3D Gaussian Splatting (3DGS) scenes. Instead of repeatedly sending the scene geometry, it transmits compact Neural Transformation Caches (NTCs) that update the Gaussians at the receiver. Saliency predictions help decide which parts of each NTC should arrive first.

The implementation extends [3DGStream](https://github.com/SJoJoK/3DGStream) with sparse INT4 NTCs, per-frame weight prioritization, and experimental QUIC streaming.

[Quickstart](docs/QUICKSTART.md) · [Configuration](docs/CONFIGURATION.md) · [Method](docs/ARCHITECTURE.md) · [Experiments](docs/EXPERIMENTS.md) · [Results](docs/RESULTS.md)

## Getting started

The command-line tools for inspecting NTC stages and running the unit tests work without CUDA:

```bash
git clone https://github.com/publioelon/Q3DGStream.git
cd Q3DGStream

python3 q3dgstream.py demo
python3 q3dgstream.py test
python3 q3dgstream.py doctor
```

The `demo` command constructs and decodes a small example of the project's `.qblk` format. To run NTC inference or render a scene, an NVIDIA GPU, PyTorch, tiny-cuda-nn, and the Gaussian rasterizer are required. See the [Ubuntu setup guide](docs/linux.md) before installing the GPU dependencies.

The [Flame Steak](docs/QUICKSTART.md) example and saved experimental checkpoints are used throughout the research code. Large models and generated data are not stored in Git. Set the dataset locations through [Configuration](docs/CONFIGURATION.md); scripts use project-relative defaults when no path is specified.

## Approach

An NTC takes Gaussian positions as input and predicts their motion for the next animation step. Q3DGStream compresses that network by retaining selected 64-weight parameter blocks and representing their values with INT4 quantization.

The retained blocks are then ordered according to their estimated influence on salient regions of the scene. We combine multiview SalFoM predictions with per-NTC gradient measurements to construct four transmission stages, `P0` through `P3`.

Each stage contains packed weights, their original block indices, and quantization scales. The receiver can reconstruct the portion of the network received so far and use it to update the Gaussians. Because successive NTCs operate on the evolving scene state, revising a partially received NTC must always start from the same pre-update Gaussian positions.

This is **application-level ordering over QUIC**. Native QUIC stream scheduling and bandwidth-driven adaptation are separate parts of the ongoing work.

## Implementation

| Path | Contents |
| --- | --- |
| `main.py`, `renderer_cuda.py`, `NTC.py` | Dynamic Gaussian viewer and NTC inference |
| `research/priority/dynamic_299/` | Saliency prediction, block ranking, and stage generation |
| `research/priority/hashgrid_ntc114/` | Block- and weight-level HashGrid dependencies, CUDA verification, and motion ablations |
| `research/quic/` | FP32 baseline, progressive QUIC experiments, and priority sender |
| `research/evaluation/` | Integrity checks and partial-reconstruction measurements |
| `scripts/`, `tests/` | Setup, GPU validation, and automated source tests |

The TCP viewer remains available as a reference implementation. The progressive QUIC receiver also depends on CUDA viewer changes tested in a separate local installation. Those changes are being integrated and checked before the full QUIC path is made the default in this repository.

## Experimental results

For the INT4 keep05 configuration, each NTC retains **1,556 blocks** of 64 parameters. A representative packed checkpoint occupies **66,741 bytes**; its four `.qblk` stages total **62,296 bytes**, excluding scene initialization and Gaussian additions. The corresponding dense FP32 network requires approximately **7.97 MB**.

We verified the stage records against the compressed checkpoints for all **299 NTC updates**. In an offline partial-reconstruction experiment, saliency-based ordering reduced relative RMS translation error in the two highest-priority regions by approximately **77% to 78%** at 75% cumulative block reception, compared with five randomized block orders.

These measurements use the **complete compressed NTC** as the reconstruction reference, rather than the original FP32 network. The 30-update QUIC pilot confirms local delivery of priority stages and Gaussian additions; full GPU playback and adaptive network performance are evaluated separately.

The evaluation scripts, protocol details, and recorded outputs are described in [Results](docs/RESULTS.md) and [Experiments](docs/EXPERIMENTS.md).

## Documentation

- [Quickstart](docs/QUICKSTART.md) covers installation and the original TCP streaming example.
- [Configuration](docs/CONFIGURATION.md) describes portable dataset, cache, and log paths.
- [Architecture](docs/ARCHITECTURE.md) describes the representation and progressive reconstruction.
- [Data formats](docs/FORMATS.md) documents the NTC checkpoints and binary `.qblk` stages.
- [QUIC](docs/QUIC.md) explains the transmission experiments and receiver requirements.
- [GPU validation](docs/GPU_VALIDATION.md) provides the CUDA and playback test procedure.
- [Contributing](CONTRIBUTING.md) describes the development and testing conventions.

## Acknowledgments

Q3DGStream builds on [3DGStream](https://github.com/SJoJoK/3DGStream), [3D Gaussian Splatting](https://github.com/graphdeco-inria/gaussian-splatting), and [tiny-cuda-nn](https://github.com/NVlabs/tiny-cuda-nn). Please refer to the original projects for their publications and licenses.

This repository is released under the [MIT License](LICENSE).
