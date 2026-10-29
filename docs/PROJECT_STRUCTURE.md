# Repository layout

- `main.py`, `renderer_cuda.py`, `NTC.py`, `live_tcp.py`, `tcp_fvv_sender.py`: original working renderer/TCP baseline.
- `q3dgstream.py`: CPU-friendly project CLI for stage decode and source tests.
- `research/priority/`: PQAT-compatible saliency-aware scheduling and HashGrid experiments.
- `research/quic/`: separate QUIC pilots and incremental NTC stage delivery.
- `research/evaluation/`: reproducibility scripts, per-frame metrics and comparisons.
- `docs/`: general documentation, file formats, experimental results and GPU validation.
- `scripts/`: installers and on-machine GPU checks.
- `tests/`: quick CPU tests and source validation.

Some research experiments require external checkpoints and saved data in their original measured paths. The project does not vendor gigabytes of data. GPU inference and live QUIC playback must be tested on a supported NVIDIA machine before release claims.
