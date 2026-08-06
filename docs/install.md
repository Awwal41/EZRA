# Installation

EZRA needs **Python 3.10+**. No GPU is required to download models; GPUs matter later for serving.

## Clone and install

```bash
git clone https://github.com/awwalola/EZRA.git
cd EZRA

python -m venv .venv

# Linux / macOS / HPC
source .venv/bin/activate

# Windows
# .venv\Scripts\activate

pip install -U pip
pip install -e .
```

For development (tests + Ruff):

```bash
pip install -e ".[dev]"
```

## Verify

```bash
ezra doctor
ezra models list
```

`ezra doctor` prints the models directory, whether a Hugging Face token is set, gallery size, and whether the models path is writable.

## Where models are stored

Default: `~/.ezra/models/<name>/` (or `$EZRA_HOME/models`).

Pick a location any of these ways (highest priority first):

| Method | Example |
|--------|---------|
| CLI flag | `ezra --models-dir /data/ezra/models models download --all` |
| Environment | `export EZRA_MODELS_DIR=/scratch/$USER/ezra/models` |
| Config file | `local.models_dir: /scratch/$USER/ezra/models` in `ezra.yaml` |
| Site profile | `ezra hpc init-site my-cluster --models-dir /scratch/$USER/ezra/models` |

On HPC, use scratch or a shared project filesystem before downloading large galleries. Confirm with `ezra doctor`.

See [Configuration](configuration.md) for all env vars and `ezra.yaml`.

## Next steps

- Download models: [Models](models.md)
- Cluster jobs: [HPC / SLURM](hpc.md)
