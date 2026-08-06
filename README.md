# EZRA
**Easy Zero-setup Routing Assistant** for local & HPC LLMs — a researcher-first system for downloading, running, and intelligently routing free/open models, purpose-built for materials science and chemistry.

> Phase 1 (this repo): curated free-model gallery + HPC-friendly one-command downloads. Router, local runtime, and science tools come next.

## Quick start

```bash
# from the repo root
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate   # Linux / macOS / HPC

pip install -e .

ezra doctor
ezra models list
```

### Download models

```bash
# one model by name
ezra models download qwen2.5-7b-instruct

# several names
ezra models download chemllm-7b matscibert chembert-uncased

# everything free in the gallery (skips gated by default)
ezra models download --all

# chemistry / materials subset
ezra models download --all --tag chemistry
ezra models download --all --science

# keep it small for a laptop smoke test
ezra models download --all --format gguf --max-size 4 --no-gated

# see what would be fetched
ezra models download --all --dry-run
```

Installed weights land under `~/.ezra/models/<name>/` (or `EZRA_MODELS_DIR`).

```bash
ezra models status
ezra models info chemllm-7b
```

## HPC (SLURM / SBATCH)

EZRA is designed to run on login nodes or batch jobs with no GUI. Use SBATCH so jobs get **GPUs, CPUs, memory, and time limits** on compute nodes (not the login node).

### One-command submit

```bash
# list built-in job kinds + default resources
ezra hpc templates

# CPU job: stage free models onto scratch
ezra hpc submit download

# GPU job: reserve a node and serve a model (OpenAI-compatible API when backends land)
ezra hpc submit serve --model qwen2.5-7b-instruct --gpus 1 --cpus 8 --mem 64G

# GPU hold for interactive work (then: srun --jobid=… --pty bash)
ezra hpc submit interactive --gpus 1 --time 02:00:00

# preview without calling sbatch (works on laptops too)
ezra hpc submit serve --model chemllm-7b --gpus 1 --dry-run
```

### Generate a script (edit partition / account, then sbatch)

```bash
ezra hpc script serve --model qwen2.5-7b-instruct --gpus 1 --partition gpu -o /tmp/ezra-serve.sh
sbatch /tmp/ezra-serve.sh
```

### Example scripts in `scripts/`

```bash
# CPU download (no GPU)
sbatch scripts/hpc_download_all.sh
MODEL=qwen2.5-7b-instruct sbatch scripts/hpc_download_all.sh

# GPU serve
MODEL=qwen2.5-7b-instruct sbatch scripts/hpc_serve_gpu.sh

# GPU interactive allocation
sbatch scripts/hpc_interactive.sh
```

Tune defaults in `ezra.yaml` under `hpc.slurm` (partition, account, per-kind cpus/mem/gpus/time).

### Inline download (login node / shared FS)

```bash
export EZRA_MODELS_DIR=/scratch/$USER/ezra/models
export HF_TOKEN=hf_xxx          # only needed for gated models (e.g. Llama 70B)

pip install -e .
ezra models download --all --no-gated --max-size 14 --workers 2
```

### Cluster environment variables

| Variable | Purpose |
|----------|---------|
| `EZRA_MODELS_DIR` | Where weights are stored (use shared / scratch FS on HPC) |
| `EZRA_HOME` | Config / state home (default `~/.ezra`) |
| `EZRA_CONFIG` | Path to `ezra.yaml` |
| `EZRA_ROOT` | Repo checkout path inside batch jobs (optional) |
| `EZRA_HOST` / `EZRA_PORT` | Bind address for serve jobs (default `0.0.0.0:8000`) |
| `EZRA_HOLD_SECONDS` | How long interactive/serve-placeholder jobs sleep |
| `EZRA_WORKERS` | Parallel download workers inside SBATCH download jobs |
| `MODEL` | Gallery model name for serve / single-model download |
| `HF_TOKEN` | Hugging Face token for gated repos |
| `CUDA_VISIBLE_DEVICES` | Set by SLURM when `--gres=gpu:…` is granted |

Site tips: uncomment `module load python/…` and `module load cuda/…` in the generated scripts, and set `hpc.slurm.partition` / `account` in config.

## CLI reference

```text
ezra doctor
ezra models list [--query TEXT] [--tag TAG] [--science] [--format gguf|safetensors]
ezra models download NAME [NAME ...]
ezra models download --all [--tag TAG] [--science] [--max-size N] [--no-gated]
ezra models info NAME
ezra models status
ezra models remove NAME
ezra hpc templates
ezra hpc script download|serve|interactive [--gpus N] [--cpus N] [--mem 64G] [-o PATH]
ezra hpc submit download|serve|interactive [--model NAME] [--gpus N] [--dry-run]
```
## Curated gallery

Models live in [`src/ezra/gallery/models.yaml`](src/ezra/gallery/models.yaml): Qwen, Llama, Mistral, DeepSeek, Gemma/Phi GGUFs for local use, plus chemistry/materials checkpoints (ChemLLM, ChemBERTa, MatSciBERT, …) and larger safetensors for GPU/HPC.

Add a model by appending an entry (name, `repo_id`, format, tags) and reinstall / re-run — no code change required.

## Vision (roadmap)

| Phase | Focus |
|-------|--------|
| **1 – Core Local** (now) | Gallery, download-by-name / download-all, HPC staging, config |
| **2 – Smart routing + HPC** | Domain classifier, policy engine, OpenAI-compatible API, remote adapters |
| **3 – Scientific layer** | Chem/materials prompts, tool-calling, RAG helpers, eval harness |
| **4 – Lab scale** | Shared configs, plugins, observability |

**One sentence:** EZRA lets materials and chemistry researchers download free LLMs, run them locally, and intelligently route between local models and HPC — without cloud lock-in.

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
