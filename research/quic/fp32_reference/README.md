# FP32 QUIC reference

This experiment sends the uncompressed Flame Steak NTC checkpoints and the original Gaussian additions over QUIC. It serves as a transport and rendering reference before introducing INT4 compression or progressive priorities.

The default sender buffers the entire sequence before playback. This is intentional: it makes it easier to compare the reconstructed scene with the original FP32 model without introducing transmission deadlines.

## Setup

Use an Ubuntu machine with the locally integrated QUIC viewer and the reference scene. The receiver requires the fixed-camera file and a local TLS certificate/key at `"$Q3DGSTREAM_TLS_CERT"` and `"$Q3DGSTREAM_TLS_KEY"`.

If the local test certificate is missing, create one:

```bash
openssl req -x509 -newkey rsa:2048 -nodes -days 7 \
  -subj '/CN=localhost' \
  -keyout "$Q3DGSTREAM_TLS_KEY" \
  -out "$Q3DGSTREAM_TLS_CERT"
```

Run the source checks and the sender preflight:

```bash
source scripts/env.sh
cd research/quic/fp32_reference

python test_package.py
bash run_sender.sh --preflight-only
```

The preflight validates required files and available storage without transferring the scene. A full FP32 sequence may require several GiB in the receiver cache.

## Transfer the scene

Run the receiver and sender in separate terminals:

```bash
# Terminal 1
cd research/quic/fp32_reference
bash run_receiver.sh
```

```bash
# Terminal 2
cd research/quic/fp32_reference
bash run_sender.sh
```

The sender places the initial Gaussian scene and first NTC checkpoint before the configuration file. This preserves the trained coordinate bounds when the receiver initializes its network. It also sends each additions file before the corresponding NTC step.

The receiver uses the dedicated `$Q3DGSTREAM_CACHE_DIR/qntc_fp32_reference_cache` and clears that cache when started. It does not clear the compressed-priority cache.

Verify a sample of the received files, then the complete cache:

```bash
python verify_reference_cache.py --sample 12
python verify_reference_cache.py
```

For a smaller smoke test, the sender supports `--frames 30 --prebuffer 30`. Restart the receiver before beginning the full transfer.

## Comparing results

The reference playback uses the original Gaussian colors, translation scale 1.0, and rotation mode `current`. The earlier measured scene bounds were `[-20, -15, 5]` to `[15, 10, 23]`.

If the file hashes match but the rendered scene differs from the source, the investigation should move to viewer state, model loading, or additions handling rather than network corruption.

This experiment checks FP32 transfer fidelity; it does not use compression or saliency-based weight ordering. Lower prebuffer settings are useful for a subsequent transmission timing experiment.
