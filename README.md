# EZRA
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-0A66C2?logo=github)](https://awwal41.github.io/EZRA/)
[![Read the Docs](https://img.shields.io/readthedocs/ezra?logo=readthedocs&label=Read%20the%20Docs)](https://ezra.readthedocs.io/)

**Easy Zero-setup Routing Assistant** for local & HPC LLMs - a researcher-first system for downloading, running, and intelligently routing free/open models, purpose-built for multi-purpose applications.

> Phase 1 (this repo): curated free-model gallery, hardware-aware recommendations, and HPC-friendly one-command downloads. Router, local runtime, and science tools come next.

**Docs:** [GitHub Pages](https://awwal41.github.io/EZRA/) · [Read the Docs](https://ezra.readthedocs.io/) · [Markdown on GitHub](docs/README.md) · [install](docs/install.md) · [models](docs/models.md) · [personal agents](docs/agents.md) · [HPC / SLURM](docs/hpc.md) · [configuration](docs/configuration.md) · [CLI](docs/cli.md)

## Quick start

```bash
# from the repo root
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate   # Linux / macOS / HPC

pip install -e .

# optional: local config / env (both gitignored — copy from *.example)
ezra init-config                  # ~/.ezra/ezra.yaml
# ezra init-config --cwd --env    # ./ezra.yaml + .env

ezra doctor
ezra models list
```

### Recommend a model for this machine

Not sure which open LLM will run well on your laptop or HPC node? EZRA probes RAM (and NVIDIA VRAM if present), then ranks gallery models that fit. Pass an optional keyword (`chemistry`, `reasoning`, `materials`, …):

```bash
ezra models recommend
ezra models recommend chemistry
ezra models recommend reasoning --limit 5
ezra models recommend --format gguf --science
```

It prints a system summary, a ranked table (why each model was chosen), and a ready-to-run download line for the top pick. Details: [docs/models.md](docs/models.md#recommend-for-this-machine).

### Download models

```bash
# after recommend, or pick a name yourself
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

Installed weights land under `~/.ezra/models/<name>/`. Choose a path with `--models-dir`, `EZRA_MODELS_DIR`, or `local.models_dir` in config.

```bash
ezra models status
ezra models info chemllm-7b
```

### Build a personal agent

Wrap EZRA with **your** system prompt and preferred gallery models (same idea as HPC site profiles — copy a template, edit, optionally share):

```bash
ezra agents init my-lab-assistant
# edit agents/my-lab-assistant/agent.yaml + prompt.md

ezra agents list
ezra agents show my-lab-assistant
ezra agents check my-lab-assistant   # validate aliases, suggest downloads
```

Starter example: [`agents/chem-assistant`](agents/chem-assistant/). Private experiments: `ezra agents init local/scratch-bot` (`agents/local/` is gitignored). Details: [docs/agents.md](docs/agents.md) · [agents/README.md](agents/README.md).

## HPC (SLURM / SBATCH)

EZRA runs on login nodes or batch jobs with no GUI. **Customize for your cluster** with a site profile (partition, account, `module load`), then commit and push so others on the same HPC benefit - see [`sites/README.md`](sites/README.md) and [docs/hpc.md](docs/hpc.md).

```bash
ezra hpc init-site my-cluster --models-dir ${SCRATCH:-$HOME}/ezra/models
# edit sites/my-cluster/ezra.yaml + modules.sh (look for EDIT ME)
export EZRA_SITE=my-cluster

ezra hpc submit download --dry-run
ezra hpc submit download --models-dir ${SCRATCH:-$HOME}/ezra/models
```

### One-command submit

```bash
ezra hpc templates
ezra hpc submit download
ezra hpc submit serve --model qwen2.5-7b-instruct --gpus 1 --cpus 8 --mem 64G
ezra hpc submit interactive --gpus 1 --time 02:00:00
ezra hpc submit serve --model chemllm-7b --gpus 1 --dry-run
```

### Generate a script

```bash
ezra hpc script serve --model qwen2.5-7b-instruct --gpus 1 --partition gpu -o /tmp/ezra-serve.sh
sbatch /tmp/ezra-serve.sh
```

### Example scripts in `scripts/`

Prefer a site profile over hand-editing these every time.

```bash
export EZRA_SITE=my-cluster
sbatch scripts/hpc_download_all.sh
MODEL=qwen2.5-7b-instruct sbatch scripts/hpc_download_all.sh
MODEL=qwen2.5-7b-instruct sbatch scripts/hpc_serve_gpu.sh
sbatch scripts/hpc_interactive.sh
```

### Cluster environment variables

| Variable | Purpose |
|----------|---------|
| `EZRA_SITE` | Site profile under `sites/<name>/` (config + modules) |
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

## CLI reference

```text
ezra doctor
ezra init-config [--home|--cwd] [--env] [--force]
ezra models list [--query TEXT] [--tag TAG] [--science] [--format gguf|safetensors]
ezra models recommend [KEYWORD] [--limit N] [--tag TAG] [--science] [--format gguf|safetensors]
ezra models download NAME [NAME ...]
ezra models download --all [--tag TAG] [--science] [--max-size N] [--no-gated]
ezra models info NAME
ezra models status
ezra models remove NAME
ezra agents list
ezra agents init NAME [--description TEXT] [--force]
ezra agents show NAME [--prompt]
ezra agents check NAME
ezra hpc templates
ezra hpc sites
ezra hpc init-site NAME
ezra hpc script download|serve|interactive [--gpus N] [--cpus N] [--mem 64G] [-o PATH]
ezra hpc submit download|serve|interactive [--model NAME] [--gpus N] [--dry-run]
```
## Curated gallery

Models live in [`src/ezra/gallery/models.yaml`](src/ezra/gallery/models.yaml): Qwen, Llama, Mistral, DeepSeek, Gemma/Phi GGUFs for local use, plus chemistry/materials checkpoints (ChemLLM, ChemBERTa, MatSciBERT, …) and larger safetensors for GPU/HPC.

Add a model by appending an entry (name, `repo_id`, format, tags) and reinstall / re-run - no code change required.

## Vision (roadmap)

| Phase | Focus |
|-------|--------|
| **1 - Core Local** (now) | Gallery, recommend-by-hardware, download-by-name / download-all, personal agent scaffolds, HPC staging, config |
| **2 - Smart routing + HPC** | Domain classifier, policy engine, OpenAI-compatible API, agent prompts wired into chat/serve, remote adapters |
| **3 - Scientific layer** | Chem/materials prompts, tool-calling, RAG helpers, eval harness |
| **4 - Lab scale** | Shared configs, plugins, observability |

**One sentence:** EZRA lets materials and chemistry researchers download free LLMs, build personal agents on top of them, run locally, and intelligently route between local models and HPC - without cloud lock-in.

## Documentation

**Published HTML:** [https://awwal41.github.io/EZRA/](https://awwal41.github.io/EZRA/) (GitHub Pages) · optional mirror [Read the Docs](https://ezra.readthedocs.io/) after you import the repo there.

User guides are Markdown under [`docs/`](docs/) (readable on GitHub). The same tree builds with **Sphinx + MyST + reStructuredText** (API autodoc, search, Furo theme). CI: [`.github/workflows/docs.yml`](.github/workflows/docs.yml) builds on PRs and deploys Pages from `main`.

```bash
pip install -e ".[docs]"
cd docs
make html          # Linux / macOS — or: .\make.bat html on Windows
# open docs/_build/html/index.html
```

How to turn Pages on / link RTD: [docs/README.md](docs/README.md#publish-so-people-get-a-link).

| Doc | Contents |
|-----|----------|
| [docs/install.md](docs/install.md) | Install, venv, `ezra doctor` |
| [docs/models.md](docs/models.md) | Recommend / list / download / status / remove |
| [docs/agents.md](docs/agents.md) | Personal agents: init / prompt / preferred models |
| [agents/README.md](agents/README.md) | In-tree agent scaffolds + chem-assistant example |
| [docs/hpc.md](docs/hpc.md) | Site profiles, scratch, `ezra hpc submit` |
| [sites/README.md](sites/README.md) | Customize for your cluster, commit & push |
| [docs/configuration.md](docs/configuration.md) | `ezra.yaml` and environment variables |
| [docs/cli.md](docs/cli.md) | Command reference (includes `models recommend`, `agents`) |
| [docs/api.rst](docs/api.rst) | Python API (Sphinx autodoc) |
| [docs/index.rst](docs/index.rst) | Sphinx site home |
| [`.github/workflows/docs.yml`](.github/workflows/docs.yml) | Build + GitHub Pages deploy |
| [.readthedocs.yaml](.readthedocs.yaml) | Optional Read the Docs build config |


## Contributing

Fork, setup, coding style, gallery additions, and PR checklist: see [CONTRIBUTING.md](CONTRIBUTING.md). Shared backlog: [TODO.md](TODO.md).

## License

GPL-3.0-or-later - see [LICENSE](LICENSE).
