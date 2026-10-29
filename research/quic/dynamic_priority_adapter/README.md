# Dynamic NTC priority streaming

This sender transmits precomputed, saliency-ordered INT4 stages over QUIC. It uses the validated `.qblk` files from `research/priority/dynamic_299/` without recomputing their order, together with the original Gaussian additions for each frame.

The pilot uses application-level priority ordering. QUIC transports the files reliably, but the code does not modify QUIC's internal stream scheduler.

## Inputs

The reference experiment uses:

- `$Q3DGSTREAM_SCENE_DIR/`, including the initial PLY and per-frame `additional_3dgs/` files.
- The INT4 keep05 PQAT experiment under `$Q3DGSTREAM_EXPERIMENT_DIR/`.
- `$Q3DGSTREAM_STAGES_DIR/`, containing four stages for each of the 299 NTCs.

The compressed and original initial scenes must match. The preflight checks their hashes, the availability of additions and stage files, block IDs, and free cache space.

## Run the 30-update pilot

The QUIC receiver must first be integrated into Q3DGStream and validated on the GPU. Follow [GPU validation](../../../docs/GPU_VALIDATION.md). Close any other process listening on UDP port 5002.

Start with the sender preflight:

```bash
cd research/quic/dynamic_priority_adapter
bash preflight.sh
```

In terminal 1, start the receiver:

```bash
bash run_receiver.sh
```

In terminal 2, from the same directory:

```bash
QNTC_STAGE_DELAY=0 bash run_sender.sh
```

The default sequence covers updates 0 through 29. The sender transfers the additions file before the four priority stages for that update. The receiver renders with the original spherical harmonics colors, rotation mode `current`, and translation scale 1.0.

The receiver clears only `$Q3DGSTREAM_CACHE_DIR/qntc_dynamic_priority_cache`. The reference FP32 cache is separate and is not deleted by this script.

Inspect the logs:

```bash
grep -E 'QUIC CPU READY|REAL QUIC ERROR|draw error|additions_' \
  "$Q3DGSTREAM_LOG_DIR/dynamic_priority_receiver.log" | tail -60

tail -40 "$Q3DGSTREAM_LOG_DIR/dynamic_priority_sender.log"
```

## Stream all updates

Once the 30-update test succeeds, stop the sender and receiver. Restart the receiver with a clean dedicated cache, then run:

```bash
QNTC_END=298 QNTC_STAGE_DELAY=0 bash run_sender.sh
```

A nonzero `QNTC_STAGE_DELAY` can make progressive steps visible. For example, `QNTC_STAGE_DELAY=0.02` adds four 20 ms pauses per NTC and limits complete updates to at most 12.5 per second before decoding, transfer, and rendering time.

## Playback and quality

The experiment prioritizes weights within the **compressed INT4 keep05 model**. Receiving P0 through P3 recovers the transmitted compressed network, not the original dense FP32 NTC.

The additions files must be present before the viewer advances to the corresponding frame. Missing additions, incorrect colors, or stale partially applied transforms are receiver-side problems to investigate in the logs. The sender's byte integrity and delivery order do not by themselves establish rendered quality or a real-time 30-update-per-second rate.

See [QUIC](../../../docs/QUIC.md) and [Results](../../../docs/RESULTS.md) for the measured scope of the experiment.
