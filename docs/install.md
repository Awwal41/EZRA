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

By default: `~/.ezra/models/<name>/`.

On HPC, point at scratch or a shared filesystem before downloading:

```bash
export EZRA_MODELS_DIR=/scratch/$USER/ezra/models
```

See [Configuration](configuration.md) for all env vars and `ezra.yaml`.

## Next steps

- Download models: [Models](models.md)
- Cluster jobs: [HPC / SLURM](hpc.md)
