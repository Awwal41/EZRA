# Installation

EZRA needs **Python 3.10+**. No GPU is required to download models; GPUs matter later for serving.

## Clone and install

```bash
git clone https://github.com/Awwal41/EZRA.git
cd EZRA
# third_party/* vendors (OpenClaw, Peekaboo, gogcli, MegaParse) are in-tree

python -m venv .venv

# Linux / macOS / HPC
source .venv/bin/activate

# Windows
# .venv\Scripts\activate

pip install -U pip
pip install -e .

# Local chat / OpenAI serve (optional extras)
pip install -e ".[local,serve]"   # GGUF via llama.cpp + FastAPI
# Apple Silicon non-GGUF (optional):
# pip install -e ".[mlx]"
# Document parsing (optional):
# pip install -e ".[parse-basic]"   # text + simple PDF
# pip install -e ".[parse]"         # MegaParse (Python ≥ 3.11)
# macOS screen capture / MCP (optional): brew install steipete/tap/peekaboo
#   sources: third_party/Peekaboo — see docs/peekaboo.md
# Google Workspace CLI (optional): brew install openclaw/tap/gogcli
#   sources: third_party/gogcli — see docs/gog.md
```

For development (tests + Ruff):

```bash
pip install -e ".[dev]"
```

On Windows, `llama-cpp-python` may need a pre-built wheel or a C++ toolchain; see the [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) docs if `pip install` fails.

## Verify

```bash
ezra doctor
ezra models list
ezra models recommend chemistry
```

`ezra doctor` prints the models directory, HF token status, gallery size, CPU/RAM/GPU fit budget, whether llama-cpp / mlx-lm / FastAPI / MegaParse are importable, Peekaboo / gog / OpenClaw (vendored) status, and whether the models path is writable.

`ezra models recommend` probes this machine and ranks open gallery models that fit (optional keyword). See [Models - Recommend](models.md#recommend-for-this-machine).

## Chat and serve (after downloading a GGUF)

```bash
ezra models download phi-3.5-mini-instruct
ezra chat --model phi-3.5-mini-instruct
ezra serve --model phi-3.5-mini-instruct --port 8000
# Point OpenAI-compatible clients at http://127.0.0.1:8000/v1
```

Dry-run without weights: `ezra chat --backend stub --model phi-3.5-mini-instruct -p "hi"`.

See [Conversation runtime](conversation.md).

## Optional: local config

```bash
ezra init-config                 # ~/.ezra/ezra.yaml (edit EDIT ME fields)
# or: ezra init-config --cwd --env   # ./ezra.yaml + .env (both gitignored)
```

On HPC, create a site profile instead: `ezra hpc init-site my-cluster`. See [HPC](hpc.md).

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

- Pick a model for this machine: [Models - Recommend](models.md#recommend-for-this-machine)
- Download models: [Models](models.md)
- Personal agents: [Agents](agents.md)
- Chat / OpenAI serve: [Conversation runtime](conversation.md)
- Parse PDFs / notes for chat: [Document parsing](parse.md)
- Cluster jobs: [HPC / SLURM](hpc.md)
