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
