# Configuration

## Customize in two minutes

| What | Easy path |
|------|-----------|
| Local paths / prefs | `ezra init-config` → edit `~/.ezra/ezra.yaml` (or `ezra init-config --cwd`) |
| Env vars / HF token | `cp .env.example .env` (or `ezra init-config --cwd --env`); `.env` is gitignored |
| HPC partition / modules | `ezra hpc init-site my-cluster` → edit `EDIT ME` → commit & push |

Do **not** commit secrets. Shareable cluster settings belong under `sites/<name>/`.

## Load order

EZRA loads settings from (first match wins for file path):

1. `--config PATH` on the CLI
2. `EZRA_CONFIG` environment variable
3. `sites/$EZRA_SITE/ezra.yaml` when `EZRA_SITE` is set (per-cluster profile)
4. `./ezra.yaml` in the current working directory (gitignored at repo root; copy from `ezra.yaml.example`)
5. `~/.ezra/ezra.yaml` (or `$EZRA_HOME/ezra.yaml`)
6. Packaged defaults: [`src/ezra/defaults/ezra.yaml`](../src/ezra/defaults/ezra.yaml)

CLI `--models-dir` and `EZRA_MODELS_DIR` override `local.models_dir` in yaml.

## Model storage location

Weights are stored under one directory (each model in a subdirectory). Choose it with:

1. **CLI** (highest priority): `ezra --models-dir /path …` or `ezra hpc submit download --models-dir /path`
2. **Environment**: `export EZRA_MODELS_DIR=/path`
3. **Config**: `local.models_dir` in `ezra.yaml` / site profile
4. **Default**: `~/.ezra/models` (or `$EZRA_HOME/models`)

```bash
# one-off download to a custom path
ezra --models-dir /data/shared/ezra/models models download qwen2.5-7b-instruct

# session-wide on HPC
export EZRA_MODELS_DIR=/scratch/$USER/ezra/models
ezra doctor

# bake into a site profile
ezra hpc init-site my-cluster --models-dir /scratch/$USER/ezra/models
```

## Site profiles (recommended on HPC)

Create a shareable cluster config (partition, account, modules) with:

```bash
ezra hpc init-site my-cluster
export EZRA_SITE=my-cluster
```

Edit `sites/my-cluster/ezra.yaml` and `modules.sh` (search for **EDIT ME**), then commit and push - see [Site profiles](sites.md) and [`sites/README.md`](../sites/README.md).

## Environment variables

| Variable | Purpose |
|----------|---------|
| `EZRA_SITE` | Name of a folder under `sites/` (loads that profile’s config + modules) |
| `EZRA_MODELS_DIR` | Where weights are stored (use scratch on HPC) |
| `EZRA_HOME` | Config / state home (default `~/.ezra`) |
| `EZRA_CONFIG` | Path to `ezra.yaml` |
| `EZRA_ROOT` | Repo checkout path inside batch jobs (optional) |
| `EZRA_HOST` / `EZRA_PORT` | Bind address for serve jobs (default `0.0.0.0:8000`) |
| `EZRA_N_GPU_LAYERS` | llama.cpp GPU layers (`-1` = all; overrides `local.n_gpu_layers`) |
| `EZRA_HOLD_SECONDS` | How long interactive/serve-placeholder jobs sleep |
| `EZRA_WORKERS` | Parallel download workers inside SBATCH download jobs |
| `MODEL` | Gallery model name for serve / single-model download |
| `HF_TOKEN` | Hugging Face token for gated repos (name configurable) |
| `CUDA_VISIBLE_DEVICES` | Usually set by SLURM when GPUs are granted |
| `EZRA_PEEKABOO_ROOT` / `EZRA_PEEKABOO_CLI` | Alternate Peekaboo tree / binary (see [Peekaboo](peekaboo.md)) |
| `EZRA_GOG_ROOT` / `EZRA_GOG_CLI` | Alternate gogcli tree / `gog` binary (see [gogcli](gog.md)) |
| `GOG_ACCOUNT` / `EZRA_GOG_ACCOUNT` | Default Google account for `ezra gog` |
| `EZRA_OPENCLAW_ROOT` / `EZRA_OPENCLAW_CLI` | Alternate OpenClaw tree / CLI (see [OpenClaw](openclaw.md)) |
| `EZRA_CLINE_ROOT` / `EZRA_CLINE_CLI` | Alternate Cline tree / CLI (see [Cline](cline.md)) |

IDE Grid is sideloaded with `ezra ide install` (no marketplace). See [IDE](ide.md).

## Example `ezra.yaml`

Start from [`ezra.yaml.example`](../ezra.yaml.example) (`ezra init-config`) or the site template.
Packaged defaults keep `hpc.enabled: false`; the block below is an **HPC-oriented**
override (turn HPC on and fill SLURM defaults):

```yaml
version: 1

local:
  backend: auto            # auto | llama | mlx | stub
  models_dir: ~/.ezra/models   # prefer EZRA_MODELS_DIR on clusters
  prefer_quant: auto
  max_workers: 2
  resume: true
  hf_token_env: HF_TOKEN
  max_loaded: 2
  n_ctx: 4096
  n_gpu_layers: -1

parse:
  backend: auto            # auto | basic | megaparse
  strategy: auto           # auto | fast | hi_res

peekaboo:
  enabled: auto            # reported by doctor/status; does not gate CLI today
  # cli: /opt/homebrew/bin/peekaboo   # or EZRA_PEEKABOO_CLI

gog:
  enabled: auto            # reported by doctor/status; does not gate CLI today
  # cli: ""                # or EZRA_GOG_CLI
  # account: you@gmail.com # or GOG_ACCOUNT / EZRA_GOG_ACCOUNT

openclaw:
  enabled: auto            # reported by doctor/status; does not gate CLI today
  # cli: ""                # or EZRA_OPENCLAW_CLI
  # EZRA never auto-starts the Gateway

cline:
  enabled: auto            # reported by doctor/status; does not gate CLI today
  # cli: ""                # or EZRA_CLINE_CLI
  # EZRA never auto-starts the agent
  # Point Cline at ezra serve (downloaded GGUFs, no cloud key):
  #   ezra cline use-local --auth

ide:
  enabled: auto            # reported by doctor/status; does not auto-install
  # ezra ide install       # sideload Grid into Cursor / VS Code

# router:                  # reserved for Phase 2 smart routing (kept in yaml)
#   mode: auto

hpc:
  enabled: true            # defaults package uses false; true here for cluster profiles
  slurm:
    partition: gpu
    # account: mylab
    # qos: normal
    download:
      time: "04:00:00"
      cpus: 4
      mem: "8G"
      gpus: 0
    serve:
      time: "08:00:00"
      cpus: 8
      mem: "64G"
      gpus: 1
    interactive:
      time: "02:00:00"
      cpus: 4
      mem: "32G"
      gpus: 1
```

`ezra hpc script` / `ezra hpc submit` read `hpc.slurm` for default walltime, CPUs, memory, and GPUs. Command-line flags (`--partition`, `--gpus`, …) override these values per job.

Notes:

- `peekaboo|gog|openclaw|cline.enabled` values show up in `ezra doctor` / `* status`; they do **not** currently block the corresponding CLI commands.
- `ide.enabled` is the same pattern; it does **not** auto-install the Grid extension.
- `router` in packaged defaults is reserved for Phase 2 domain routing (agents may still reference prefs via `agent.yaml`).
- `local.keep_alive` appears in packaged defaults as a future knob; it is not applied by the loader yet.

## Hugging Face token

Gated models need a token and an accepted license on the model page:

```bash
export HF_TOKEN=hf_xxx
ezra doctor   # should show "HF token set: yes"
```

The env var name defaults to `HF_TOKEN` and can be changed via `local.hf_token_env` in config. Do **not** commit tokens into site profiles.
