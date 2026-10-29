# Source layout

The repository keeps the viewer, model code, research experiments, and tests in separate directories.

| Location | Purpose |
| --- | --- |
| `main.py`, `renderer_cuda.py`, `renderer_ogl.py` | Dynamic Gaussian viewer and renderers |
| `NTC.py`, `quantize_ntcs.py` | Neural Transformation Cache and quantization utilities |
| `live_tcp.py`, `tcp_fvv_sender.py` | Reference TCP streaming path |
| `q3dgstream.py` | Small command-line interface for stage inspection and tests |
| `research/priority/` | Saliency, HashGrid influence, and block ranking experiments |
| `research/quic/` | QUIC transport and progressive receiver experiments |
| `research/evaluation/` | Compression and reconstruction measurements |
| `scripts/` | Setup, synchronization, and GPU validation tools |
| `tests/` | Python source and binary format tests |
| `docs/` | Installation notes, method, formats, and results |

Scene files, NTC weights, Gaussian state snapshots, and generated prediction data are external inputs. They are not included in the repository because of their size.

The standalone format tests work without CUDA. NTC inference and QUIC rendering must be tested with a compatible GPU and the saved experimental assets. For commands, see [Quickstart](QUICKSTART.md) and [GPU validation](GPU_VALIDATION.md).
