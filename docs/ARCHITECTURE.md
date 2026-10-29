# Architecture

Q3DGStream follows the dynamic scene representation introduced by 3DGStream. A Gaussian scene is initialized once and updated over time using one Neural Transformation Cache (NTC) per animation step. The current experiments concentrate on compressing these NTCs and deciding which of their parameters to send first.

## Dynamic Gaussian updates

Each persistent Gaussian has a position, rotation, scale, opacity, and appearance. For an animation step, an NTC takes Gaussian positions as input and predicts translation and quaternion updates. The network uses a multiresolution HashGrid encoding followed by an MLP.

NTCs are applied **in temporal order**. The Gaussian state after frame *t* becomes the input state for frame *t + 1*. New Gaussians from the corresponding additions file are handled separately from the persistent set.

## Sparse NTC representation

The original dense NTC contains 1,991,680 parameters. The INT4 keep05 experiment retains 1,556 blocks of 64 weights (5% of the dense blocks). Each retained block has a scale and 32 bytes of packed four-bit values.

PQAT combines block pruning with quantization-aware training. The resulting source checkpoint is encoded as a set of indexed records for transmission. See [Formats](FORMATS.md) for the `.qblk` layout.

## Saliency and priority assignment

Saliency identifies regions likely to attract attention in the rendered scene. The current pipeline uses saved predictions from 12 camera views, combines them into spatial importance, and interpolates the available temporal anchors.

For each NTC, gradient-based probes estimate how strongly retained weight blocks influence selected spatial Gaussian groups. Blocks that matter to high-priority regions move earlier in the transmission order. A frame's retained weights are divided into four stages: P0, P1, P2, and P3.

HashGrid blocks can contribute to many Gaussians. A stage is therefore **a set of neural parameters**, not a visible 3D tile. The NTC 114 experiments map both blocks and individual retained HashGrid weights to the Gaussians accessing them. The finer map records interpolation coefficients; selected-weight ablations separately measure changes in predicted motion. See [HashGrid analysis](../research/priority/hashgrid_ntc114/README.md).

## Progressive reconstruction

The receiver collects weight records, restores each block to its original parameter indices, and evaluates the partially available NTC. After receiving another stage, it can refine the estimate.

One rule is essential: **all refinements of a frame must use the same pre-update Gaussian positions**. Applying the P0 displacement, then applying P1 to the already displaced state, would count the motion twice. Only the selected state transition should advance the animation.

A missing or late NTC step is different from an incomplete NTC. The former changes the age of the scene state; the latter changes the number of available model parameters.

## Transport

The initial scene and metadata are followed by Gaussian additions and staged NTC updates. QUIC carries the files reliably; the current pilot selects their order in application code. Scheduling based on bandwidth, deadlines, and NTC state age is a distinct development direction.

The [QUIC guide](QUIC.md) describes the live prototype, while [Experiments](EXPERIMENTS.md) covers the per-NTC reconstruction tests. A shared time-conditioned NTC would reduce redundancy between frames, but is not implemented in this version.
