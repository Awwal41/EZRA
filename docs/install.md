# Installation

EZRA needs **Python 3.10+**. No GPU is required to download models; GPUs matter later for serving.

**Prefer a checklist?** [Getting started](getting-started.md) walks from zero to the VS Code extension and tells you **which wheel file** to install.

## Clone and install

```bash
git clone https://github.com/Awwal41/EZRA.git
cd EZRA
# third_party/* vendors (OpenClaw, Peekaboo, gogcli, MegaParse, Cline, Voicebox) are in-tree

python -m venv .venv

# Linux / macOS / HPC
source .venv/bin/activate

# Windows
# .venv\Scripts\activate

pip install -U pip
pip install -e .

# Chat + Grid (pick ONE wheel file — do not compile llama.cpp from source on Windows)
pip install -r requirements-ide-cpu.txt          # no NVIDIA GPU
# pip install -r requirements-ide-cuda124.txt    # NVIDIA, CUDA 12.4 (see nvidia-smi)
# pip install -r requirements-ide-cuda121.txt    # NVIDIA, CUDA 12.1
# pip install -r requirements-ide-macos.txt      # Apple Silicon

# Same extras without a wheel file (may compile; often fails on Windows):
# pip install -e ".[local,serve]"
# Apple Silicon non-GGUF (optional, also in requirements-ide-macos.txt):
# pip install -e ".[mlx]"
# Document parsing (optional):
# pip install -e ".[parse-basic]"   # text + simple PDF
# pip install -e ".[parse]"         # MegaParse (Python ≥ 3.11)
# macOS screen capture / MCP (optional): brew install steipete/tap/peekaboo
#   sources: third_party/Peekaboo — see docs/peekaboo.md
# Google Workspace CLI (optional): brew install openclaw/tap/gogcli
#   sources: third_party/gogcli — see docs/gog.md
# Coding agent CLI (optional; Cline lane only — skip for Local chat):
#   npm i -g cline
#   or Bun 1.3+ / vendored build / EZRA_CLINE_CLI — see docs/cline-local.md
#   sources: third_party/Cline — see docs/cline.md
# Voicebox AI voice studio / MCP (optional): start the app yourself
#   sources: third_party/Voicebox — see docs/voicebox.md
#   ezra voicebox mcp-config
```

Wheel files live next to `requirements.txt`. Table: [`requirements/README.md`](../requirements/README.md).

For development (tests + Ruff):

```bash
pip install -e ".[dev]"
```

On Windows, **do not** let pip compile `llama-cpp-python` from source. If you see `Building wheel for llama-cpp-python` for more than a minute, Ctrl+C and use `requirements-ide-cpu.txt`. Upstream notes: [llama-cpp-python](https://github.com/abetlen/llama-cpp-python).

## Verify

```bash
ezra doctor
ezra models list
ezra models recommend chemistry
```

`ezra doctor` prints the models directory, HF token status, gallery size, CPU/RAM/GPU fit budget, whether llama-cpp / mlx-lm / FastAPI / MegaParse are importable, Peekaboo / gog / OpenClaw / Cline / Voicebox (vendored) status, and whether the models path is writable.

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

- First-time, including VS Code: [Getting started](getting-started.md)
- Pick a model for this machine: [Models - Recommend](models.md#recommend-for-this-machine)
- Download models: [Models](models.md)
- Personal agents: [Agents](agents.md)
- Chat / OpenAI serve: [Conversation runtime](conversation.md)
- VS Code sidebar chat (not Copilot): [EZRA Grid](ide.md#2-open-the-grid-and-chat-vs-code)
- Parse PDFs / notes for chat: [Document parsing](parse.md)
- Cluster jobs: [HPC / SLURM](hpc.md)
