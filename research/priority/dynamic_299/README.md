# Saliency-aware NTC block ranking

This experiment generates a transmission order for the retained INT4 weight blocks of each NTC in the 299-update Flame Steak sequence. It prepares the weights for progressive delivery; it does not send them over QUIC.

The implementation uses an independent block ranking for each NTC, rather than assuming that NTC 114's sensitivity map remains valid for the rest of the animation.

## Ranking procedure

The saliency timeline is built from 36 saved fused 3D SalFoM anchors obtained from 12 camera views. Scores between the anchors are interpolated. The scene's 280,768 persistent Gaussians are partitioned into 32 spatial groups.

For each NTC, the program loads the INT4 keep05 checkpoint, reconstructs the retained weights, and probes the network with tiny-cuda-nn to estimate the sensitivity of the Gaussian groups to its parameter blocks. Those measurements are combined with the frame's saliency scores.

Priority is assigned to spatial groups first: two highest-ranked groups belong to P0, the next two to P1, four nearby groups to P2, and the rest to P3. The retained network blocks are ordered by their estimated influence on these groups. Shared HashGrid parameters can affect several groups; MLP blocks are sent first when retained.

## Run

Activate the installed CUDA environment, then use the scripts in this directory:

```bash
source scripts/env.sh
cd research/priority/dynamic_299

bash run_pilot.sh
bash run_small_sequence.sh
bash run_all.sh
```

The pilot tests NTC 114. The next command checks the small range 112 through 116. The full run ranks updates 0 through 298 and checks the emitted stage files.

To process an individual range:

```bash
python rank_ntc_frames.py --start 110 --end 118 --emit-stages
python check_schedule.py --start 110 --end 118 --stages
```

The default output directory is `$Q3DGSTREAM_PRIORITIES_DIR/`:

- `orders/NTC_XXXXXX.npz` contains the block ranking and spatial group priorities.
- `stages/NTC_XXXXXX_P0.qblk` through `P3.qblk` contain the original indexed 40-byte INT4 records.
- `check_schedule.py` verifies that the staged records match the source compressed checkpoint.

## Notes on the measurement

Sensitivity is estimated using randomized output-gradient probes. The current ranking uses sampled **initial positions** of persistent Gaussians, not the updated positions at every animation step. Thus, the per-NTC network weights change during ranking while the sampled spatial positions remain fixed.

Newly added per-frame Gaussians are outside the persistent-Gaussian grouping. Their handling belongs to the scene update and playback paths.

The full run is computationally intensive: up to 299 NTCs × 32 groups × two gradient probes, with up to 128 Gaussian samples per group. It processes checkpoints sequentially and skips completed outputs. The stages preserve the compressed INT4 model; their ordering does not replace blocks that pruning removed.

See [architecture](../../../docs/ARCHITECTURE.md), [stage format](../../../docs/FORMATS.md), and [evaluation](../../../docs/EXPERIMENTS.md).
