# Data formats

Q3DGStream uses the original 3DGStream scene files together with compressed NTC checkpoints and a binary format for transmitting prioritized weight blocks.

| Extension | Contents |
| --- | --- |
| `.ply` | Initial Gaussian scene and frame-specific additions |
| `.pth` | PyTorch NTC checkpoints, including dense, compressed wire, and decoded runtime representations |
| `.qblk` | One priority stage containing indexed INT4 NTC weight blocks |
| `.npz` | Saved priority orders and structural mapping data |
| `.pt` | Gaussian states saved for offline evaluation |
| `.json` | NTC configuration, bounds, timelines, and verification metadata |

The project stores different kinds of `.pth` checkpoints. A compressed wire checkpoint is not interchangeable with a dense FP32 checkpoint: the loading code must handle its block indices, packed values, and scales.

## `.qblk` priority stages

`.qblk` is the binary record format used in the current progressive QUIC experiments. The file starts with a **14-byte header**, encoded in network byte order:

```python
struct.Struct("!5sIBHH")
```

| Field | Bytes | Description |
| --- | ---: | --- |
| Magic | 5 | `QNP01` |
| Frame index | 4 | NTC update to which the stage belongs |
| Stage index | 1 | 0 to 3 (P0 to P3) |
| Total blocks | 2 | Number of retained blocks in the complete compressed NTC |
| Stage blocks | 2 | Number of records in this file |

The header is followed by `Stage blocks` fixed-size **40-byte records**:

```python
struct.Struct("!If32s")
```

Each record stores a four-byte original parameter block index, a four-byte FP32 quantization scale, and 32 bytes of packed four-bit weights. Every byte contains two weight values, with the low nibble representing the first value.

Dequantization uses `q = nibble - 8`, so the signed integer range is from -8 to 7. The reconstructed weight is `scale * q`.

A complete keep05 model contains 1,556 records of 64 weights. Consequently, the four stages together occupy `1,556 * 40 + 4 * 14 = 62,296` bytes, not counting metadata and transport overhead outside the stage files.

## Reconstructing an NTC

A decoder must restore each weight block to its original offset in the network parameter array. Blocks that have not yet arrived are zero until their records are received. The same block index must not appear more than once across stages of a frame.

Priority stages are **not Gaussian geometry tiles**. A HashGrid parameter block can affect many Gaussians, which is why the ordering process measures the spatial influence of the neural parameters.

Use `python3 q3dgstream.py inspect-stage PATH` to check the header and individual records of a generated file. See [Architecture](ARCHITECTURE.md) for how these weights are used during playback.
