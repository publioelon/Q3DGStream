# Dataset and environment configuration

Q3DGStream keeps source code separate from scene assets, checkpoints, intermediate files, and local TLS credentials. By default, external data belongs under `data/` at the repository root. That directory is ignored by Git.

Scripts use `q3dg_paths.py` (Python) and `scripts/env.sh` (Bash) to resolve the same locations. You can use the default directory layout or override individual paths with environment variables.

## Default layout

```text
Q3DGStream/
  data/
    scenes/flame_steak/         # Initial scene, NTCs and additions
    experiments/int4_keep05/   # Compressed checkpoint experiment
    priorities/                # Priority schedules and stages
    states/                    # Saved Gaussian states
    saliency/                  # Raw saliency and timeline
    hashgrid/                  # Gaussian-to-block mapping
    cache/                     # Receiver caches
    logs/                      # Test and playback logs
    local/                     # Local QUIC TLS keys
```

The training checkpoints, predictions, and saved states are **not** included in this repository.

## Point to existing datasets

For datasets stored elsewhere, export the corresponding variables before running the scripts:

```bash
export Q3DGSTREAM_SCENE_DIR=/path/to/flame_steak
export Q3DGSTREAM_EXPERIMENT_DIR=/path/to/int4_keep05
export Q3DGSTREAM_PRIORITIES_DIR=/path/to/priorities
export Q3DGSTREAM_STATES_DIR=/path/to/gaussian_states
export Q3DGSTREAM_SALIENCY_DIR=/path/to/salfom_predictions
```

Alternatively, set only `Q3DGSTREAM_DATA_DIR=/path/to/datasets` if your files follow the default layout above.

More specific overrides are available: `Q3DGSTREAM_COMPRESSED_SCENE_DIR`, `Q3DGSTREAM_WIRE_DIR`, `Q3DGSTREAM_STAGES_DIR`, `Q3DGSTREAM_TIMELINE_FILE`, `Q3DGSTREAM_HASHGRID_MAP`, `Q3DGSTREAM_TILE_SUPPORT_FILE`, `Q3DGSTREAM_CACHE_DIR`, and `Q3DGSTREAM_LOG_DIR`.

Environment variables take precedence over the defaults. Use **absolute paths** when pointing to data outside the repository. None of these variables needs to be committed.

## Python environment

Install a new Python environment with `./scripts/setup_linux_venv.sh`. The default is a local `.venv/` directory. To reuse an existing environment, activate it before executing the scripts:

```bash
source /path/to/virtualenv/bin/activate
source scripts/env.sh
python3 q3dgstream.py doctor
```

`scripts/env.sh` will also activate the local `.venv/` if no environment is active. It exports the data, cache, and TLS locations for the Bash launchers.

## Local QUIC certificate

The receiver reads `Q3DGSTREAM_TLS_CERT` and `Q3DGSTREAM_TLS_KEY` (by default under `data/local/`). You can generate a local test certificate:

```bash
source scripts/env.sh
mkdir -p "$(dirname "$Q3DGSTREAM_TLS_CERT")" "$(dirname "$Q3DGSTREAM_TLS_KEY")"
openssl req -x509 -newkey rsa:2048 -nodes -days 7 \
  -subj '/CN=localhost' \
  -keyout "$Q3DGSTREAM_TLS_KEY" \
  -out "$Q3DGSTREAM_TLS_CERT"
```

These keys are for local testing and must never be committed. The stage generation and evaluation scripts do not require a certificate.

See [Quickstart](QUICKSTART.md) for the baseline viewer or [GPU validation](GPU_VALIDATION.md) for compressed NTC and QUIC playback checks.
