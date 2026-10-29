# HashGrid block influence for NTC 114

This experiment maps retained HashGrid parameter blocks to the persistent Gaussians that can read them during NTC inference. The result is a **structural dependency map**: it identifies which blocks are accessed, not the magnitude of their contribution to rendered motion.

The implementation follows the multiresolution HashGrid indexing used by tiny-cuda-nn. Before writing the full map, it checks sampled results against gradients from the installed CUDA encoding. A mismatch causes the run to stop.

## Run

```bash
source scripts/env.sh
cd research/priority/hashgrid_ntc114

bash run_pilot.sh --verify-only
bash run_pilot.sh
```

For a shorter first test:

```bash
bash run_pilot.sh --max-gaussians 4096 \
  --out "$Q3DGSTREAM_HASHGRID_DIR/smoke"
```

By default, the full map is written to `$Q3DGSTREAM_HASHGRID_DIR/`.

| Output | Contents |
| --- | --- |
| `ntc_114_hash_block_to_gaussian_ids.npz` | Block-to-Gaussian lookup in compressed sparse-row form |
| `ntc_114_block_counts.csv` | Number of potentially affected Gaussians per retained block |
| `ntc_114_report.json` | Block totals and verification summary |

For a block ID, the compressed lookup stores its Gaussian IDs in `gaussian_ids[offsets[i]:offsets[i+1]]`, where `i` is the corresponding position in `block_ids`.

Inspect one block with:

```bash
python query_block.py 128
```

## Interpretation

The map uses the **initial positions** of the persistent Flame Steak Gaussians. It does not use the displaced positions immediately before NTC 114, and it does not include newly added Gaussians.

A recorded dependency means that the HashGrid encoding reads a parameter at that coordinate. The final displacement may still be zero after quantization or MLP decoding. MLP blocks have a wider potential influence and are handled separately.

The CUDA verification is part of the experiment's correctness check. If it fails, inspect the installed tiny-cuda-nn version and the grid indexing assumptions rather than disabling the check.

The indexing reference is the tiny-cuda-nn implementation in `include/tiny-cuda-nn/encodings/grid.h` and `include/tiny-cuda-nn/common_device.h`. The experiment reads its source models and scene data without modifying them.

## Individual-weight mapping

The `map_individual_weights.py` experiment works at the **feature-weight level** rather than the 64-weight block level. For each retained HashGrid weight it records the Gaussian IDs accessing that parameter and the sum of its trilinear interpolation coefficients. Hash collisions are combined before writing the mapping.

Unlike the earlier block experiment, this run defaults to the **saved Gaussian positions immediately before NTC 114** (`state_000114.pt`). This matters because Gaussian motion can change which HashGrid vertices are accessed. `--positions initial` is available for a direct comparison with the original block-level map.

First configure your saved scene, compressed checkpoints, and Gaussian states as described in [Configuration](../../../docs/CONFIGURATION.md). Use the existing CUDA environment and run these commands from the repository root:

```bash
source scripts/env.sh

# Small GPU check before indexing the full scene.
python research/priority/hashgrid_ntc114/map_individual_weights.py \
  --ntc 114 --max-gaussians 4096 --cuda-probes 12 \
  --out "$Q3DGSTREAM_OUTPUT_DIR/weight_smoke"

# Full weight-to-Gaussian map, plus sampled numerical influence.
python research/priority/hashgrid_ntc114/map_individual_weights.py \
  --ntc 114 --cuda-probes 12 \
  --sensitivity-gaussians 2048 --sensitivity-probes 2 \
  --ablate-top 16 --ablate-limit 256
```

This experiment runs on **one GPU**. The indexing itself uses CPU/NumPy; the CUDA checks use tiny-cuda-nn. Gradients and weight ablations run in bounded GPU batches. It does not modify the scene, model checkpoints, or viewer.

Outputs are written to `$Q3DGSTREAM_HASHGRID_DIR/individual/` by default:

| Output | Description |
| --- | --- |
| `ntc_114_weight_to_gaussian_state.npz` | CSR mapping with exact weight IDs, Gaussian IDs, and interpolation coefficients |
| `ntc_114_weight_counts.csv` | Number of accessing Gaussians for each retained HashGrid weight |
| `ntc_114_weight_sensitivity.csv` | Sampled first-order squared-gradient scores for all retained HashGrid weights |
| `ntc_114_ablations.csv` | Per-Gaussian motion differences when a selected weight is zeroed |
| `ntc_114_weight_report.json` | Map size, CUDA checks, and numerical experiment summary |

A short lookup for one weight:

```bash
python research/priority/hashgrid_ntc114/query_weight.py 8192 --limit 20
```

Export all Gaussian IDs associated with that weight:

```bash
python research/priority/hashgrid_ntc114/query_weight.py 8192 \
  --export "$Q3DGSTREAM_OUTPUT_DIR/weight_8192_gaussians.csv"
```

**What the measurements mean.** The mapping describes exact *HashGrid input dependencies*. Its coefficients describe interpolation, **not displacement**. The CUDA checks compare the individual parameter indices with tiny-cuda-nn gradients. The sensitivity scores approximate the influence of removing weights on sampled NTC motion outputs; the ablation rows measure the change in translation and normalized quaternion update when one weight is actually set to zero. For the ablation experiment, the 16 default candidates are chosen by structural Gaussian coverage, not by numerical importance.

The 9 retained MLP blocks remain global neural connections and are not represented in this local HashGrid map. Measuring all weight–Gaussian pairs with individual finite-difference ablations would be considerably more expensive than generating the complete structural lookup, so the first numerical comparison uses sampled Gaussians and selected weights.

The saved state and all model files stay outside Git. If you explicitly run `--skip-cuda-check`, the output marks the index map as **not GPU-verified**.
