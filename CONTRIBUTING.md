# Contributing

Q3DGStream is research code for dynamic 3DGS compression and streaming. Small, reproducible changes are easier to review than changes to several experiments at once.

## Before submitting a change

The format parser and most source tests run on Python 3.10 or later without a GPU:

```bash
python3 q3dgstream.py test
python3 q3dgstream.py demo
python3 -m compileall -q q3dgstream.py research scripts tests
```

For changes to CUDA inference, the rasterizer, or the QUIC receiver, also run the [GPU validation procedure](docs/GPU_VALIDATION.md). Include the GPU model, driver, PyTorch/CUDA versions, and the exact command used to reproduce the result.

## Code and experiments

Keep viewer changes near `main.py` and `renderer_cuda.py`. Compression, saliency, transport, and analysis scripts belong under `research/`.

A new experiment should record its inputs, checkpoint format, random seeds, frame range, and output path. Expose machine-specific directories as arguments where possible rather than embedding them in new scripts.

In results, distinguish pruning ratio from stage reception ratio, PTQ from PQAT, and the complete compressed NTC from the FP32 reference. When reporting visual metrics, identify the sequence, rendering protocol, and evaluated frames.

Do not commit model weights, scene PLYs, prediction datasets, local camera calibration files, or private TLS keys. Keep generated outputs outside the repository or in ignored directories.

## Dependencies and attribution

Preserve the original project licenses and attribution when incorporating third-party source code. If an external dependency changes, record its tested version or commit so the experiment can be repeated.
