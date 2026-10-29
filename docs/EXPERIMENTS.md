# Reproducing the experiments

The scripts under `research/` use the Flame Steak sequence and a saved INT4 keep05 PQAT run. The scene geometry, NTC checkpoints, saved Gaussian states, SalFoM predictions, and generated stage files are external inputs, not part of the Git repository.

CUDA inference uses PyTorch and tiny-cuda-nn. Start with [Ubuntu installation](linux.md) and [GPU validation](GPU_VALIDATION.md) if the machine has not been prepared.

## Priority generation

`research/priority/dynamic_299/` contains the SalFoM timeline preparation, per-frame sensitivity measurements, and stage writer.

```bash
cd research/priority/dynamic_299
python3 test_offline.py
bash run_pilot.sh
bash run_small_sequence.sh
bash run_all.sh
```

The pilot ranks NTC 114 first. The full run extends the procedure to all 299 NTCs and emits four `.qblk` files per frame. It uses 36 saved multiview saliency anchors with interpolation between them, rather than independent SalFoM inference at every animation frame.

The full run carries out per-frame gradient measurements and is substantially more expensive than the format tests. Its scripts support continuing from already generated outputs.

## Verify the transmitted records

From the repository root, check an individual stage:

```bash
python3 q3dgstream.py inspect-stage \
  "$Q3DGSTREAM_STAGES_DIR/NTC_000114_P0.qblk"
```

To compare all 299 stage sets against the compressed wire checkpoints:

```bash
python3 research/evaluation/qntc_299_priority_eval.py \
  --verify-only --out "$Q3DGSTREAM_OUTPUT_DIR/wire_verification"
```

The verification checks original block indices, FP32 scales, and packed INT4 bytes, rather than comparing only the decoded tensor's approximate values.

## Evaluate progressive reconstruction

A short GPU run over three consecutive NTCs:

```bash
python3 research/evaluation/qntc_299_priority_eval.py \
  --start 113 --end 115 --seeds 5 --batch 8192 \
  --out "$Q3DGSTREAM_OUTPUT_DIR/eval_113_115"
```

For the complete sequence:

```bash
python3 research/evaluation/qntc_299_priority_eval.py \
  --start 0 --end 298 --seeds 5 --batch 8192 \
  --out "$Q3DGSTREAM_OUTPUT_DIR/eval_299"
```

The evaluator computes the NTC transformation for saved Gaussian input states. Saliency-prioritized block reception is compared with five randomized orders. Each frame's partial NTC is compared against the **full compressed NTC for that same frame**.

For rotation analysis, use `research/evaluation/qntc_299_priority_eval_rotation_v2.py`, which makes the zero-length quaternion fallback explicit. Viewport and rendered-image evaluation require a separately controlled rendering protocol.

## Saved results

`research/results/wire_stage_verification.json` records the 299-stage integrity check. `research/results/metrics_113_115.csv` contains the small reconstruction sample. The full experiment's large datasets and output traces are not distributed through Git.

The [Results](RESULTS.md) page summarizes completed measurements and distinguishes the older 50-frame image-quality evaluation from the later 299-update protocol.
