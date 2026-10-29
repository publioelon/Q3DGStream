# Q3DGStream

*Saliency-Driven Adaptive Streaming of Dynamic 3D Gaussian Splatting over QUIC*

Q3DGStream investigates how to stream dynamic 3D Gaussian Splatting (3DGS) scenes while reducing the amount of data sent for each animation frame. The initial Gaussian scene is transmitted once; subsequent motion is represented by Neural Transformation Caches (NTCs) that the receiver evaluates locally.

The work combines pruning-preserving quantization-aware training (PQAT), saliency-based ordering of NTC weight blocks, and progressive delivery over QUIC. The aim is to make useful motion information available earlier when bandwidth is limited.

## How it works

Each NTC predicts changes in Gaussian positions and rotations. Rather than send the full network at every step, we retain selected parameter blocks and encode their weights in INT4. A per-frame priority schedule then determines the order in which these blocks are transmitted.

The compressed weights are stored in four successive priority stages, P0 through P3, using the project's `.qblk` format. The receiver can reconstruct a partial NTC from the stages received so far and evaluate it against the corresponding Gaussian state.

The stages are not independent pieces of geometry: they are parts of a neural network. Progressive reconstruction must use the same input state for each revision of a frame's NTC.

## Repository contents

- `main.py`, `renderer_cuda.py`, `NTC.py`: 3DGS viewer and NTC inference.
- `research/priority/`: saliency-based block ranking, stage generation, and HashGrid analysis.
- `research/quic/`: QUIC senders and progressive reception experiments.
- `research/evaluation/`: stage verification and reconstruction accuracy measurements.
- `q3dgstream.py`: lightweight commands for inspecting the binary format and running source tests.

The original viewer's TCP path is retained as a baseline. The newer QUIC receiver uses additional locally tested CUDA and receiver-side changes, which are being validated in this repository before being treated as the default playback path.

## Getting started

Clone the repository and run the format demo and tests:

```bash
git clone https://github.com/publioelon/Q3DGStream.git
cd Q3DGStream
python3 q3dgstream.py demo
python3 q3dgstream.py test
```

These checks do not require a GPU. For experiments on Ubuntu with NVIDIA CUDA, see the [Linux installation guide](docs/linux.md) and [GPU validation instructions](docs/GPU_VALIDATION.md). If you already have a working `qntcstream` environment, reuse it rather than reinstalling the CUDA stack.

To check the current environment:

```bash
source ~/venvs/qntcstream/bin/activate
python3 q3dgstream.py doctor
```

The original TCP playback commands are documented in [Quickstart](docs/QUICKSTART.md). The progressive QUIC experiments and their requirements are covered in [QUIC](docs/QUIC.md).

## Current results

The INT4 keep05 configuration retains 1,556 blocks of 64 weights per NTC. A representative compressed checkpoint is 66,741 bytes, compared with approximately 7.97 MB for the dense FP32 checkpoint. Its four `.qblk` stages together contain 62,296 bytes of weight records and stage headers.

The stage records were checked against the compressed checkpoints for all 299 NTC updates. In the separate partial-reconstruction evaluation, saliency-guided ordering reduced relative RMS translation error by approximately 77% to 78% in the two highest-priority regions at 75% cumulative block reception, compared with five random block orders.

These are results from the compressed NTC representation and offline reconstruction experiments. The live QUIC pilot has been exercised over a local connection; GPU playback integration and network-adaptation measurements are separate tests.

Details of the experimental setup and measurements are in [Results](docs/RESULTS.md) and [Experiments](docs/EXPERIMENTS.md).

## Documentation

- [Architecture](docs/ARCHITECTURE.md): NTC inference, compression, saliency ranking, and reconstruction.
- [Formats](docs/FORMATS.md): INT4 weights and the `.qblk` stage layout.
- [Quickstart](docs/QUICKSTART.md): installation and baseline playback.
- [QUIC](docs/QUIC.md): progressive transmission experiments.
- [GPU validation](docs/GPU_VALIDATION.md): CUDA inference and live playback checks.
- [Contributing](CONTRIBUTING.md): development notes.

Q3DGStream builds on the dynamic scene representation and viewer from [3DGStream](https://github.com/SJoJoK/3DGStream). The repository is distributed under the [MIT License](LICENSE).
