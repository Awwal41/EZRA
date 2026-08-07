# HPC / SLURM

EZRA is meant to run on login nodes or batch jobs with no GUI. Use **SBATCH** so downloads and (later) serve jobs get CPUs, memory, GPUs, and time limits on compute nodes.

**Every cluster is different.** Customize once with a **site profile**, then commit and push it so others on the same HPC can reuse your partition, modules, and notes. See [`sites/README.md`](sites.md).

## Customize for your HPC (do this first)

```bash
cd /path/to/EZRA
source .venv/bin/activate

ezra hpc init-site my-cluster --models-dir /scratch/$USER/ezra/models
$EDITOR sites/my-cluster/ezra.yaml     # EDIT ME: partition, account, gpus, mem
$EDITOR sites/my-cluster/modules.sh    # EDIT ME: module load python/cuda/…
$EDITOR sites/my-cluster/NOTES.md      # scratch path, docs link for the next person

export EZRA_SITE=my-cluster
# Or skip --models-dir above and set:
# export EZRA_MODELS_DIR=/scratch/$USER/ezra/models
ezra doctor
ezra hpc submit download --dry-run     # confirm resources before submitting
```

Then share it:

```bash
git checkout -b sites/my-cluster
git add sites/my-cluster
git commit -m "Add my-cluster SLURM site profile"
git push -u origin sites/my-cluster
# open a PR - no tokens or private secrets
```

`export EZRA_SITE=…` makes `ezra hpc submit` and `scripts/hpc_*.sh` load that folder’s `ezra.yaml` + `modules.sh`.

## Recommended setup

```bash
cd /path/to/EZRA
source .venv/bin/activate   # or create the venv as in install.md

export EZRA_SITE=my-cluster              # after init-site
export EZRA_MODELS_DIR=/scratch/$USER/ezra/models
export EZRA_HOME=/scratch/$USER/ezra

# Optional: gated Hugging Face models
# export HF_TOKEN=hf_xxx

ezra doctor
ezra hpc sites
```

## Option A - download on the login node

Fine for a few small models if the login node allows outbound HTTPS and you have enough quota:

```bash
ezra models download --all --no-gated --max-size 14 --workers 2
ezra models status
```

Prefer a batch job for large galleries or slow networks.

## Option B - one-command submit

```bash
ezra hpc templates
ezra hpc submit download --models-dir /scratch/$USER/ezra/models
ezra hpc submit download --model qwen2.5-7b-instruct
ezra hpc submit download --dry-run
```

GPU jobs (when serve backends land):

```bash
ezra hpc submit serve --model qwen2.5-7b-instruct --gpus 1 --cpus 8 --mem 64G
ezra hpc submit interactive --gpus 1 --time 02:00:00
```

CLI flags (`--partition`, `--account`, `--gpus`, …) override the site profile for a single job.

## Option C - generate a script, then sbatch

```bash
ezra hpc script download -o /tmp/ezra-dl.sh
sbatch /tmp/ezra-dl.sh
```

## Option D - example scripts in `scripts/`

These are generic fallbacks. Prefer a site profile so you do not re-edit `#SBATCH` lines every time.

```bash
export EZRA_SITE=my-cluster
sbatch scripts/hpc_download_all.sh
MODEL=qwen2.5-7b-instruct sbatch scripts/hpc_download_all.sh
MODEL=qwen2.5-7b-instruct sbatch scripts/hpc_serve_gpu.sh
sbatch scripts/hpc_interactive.sh
```

## Job kinds

| Kind | Typical use | Default resources (from packaged config) |
|------|-------------|------------------------------------------|
| `download` | Stage gallery weights (CPU) | 4 CPUs, 8G, 4h, 0 GPUs |
| `serve` | Hold a GPU node + model env for serving | 8 CPUs, 64G, 8h, 1 GPU |
| `interactive` | Interactive GPU allocation | 4 CPUs, 32G, 2h, 1 GPU |

Defaults come from `hpc.slurm` in your site `ezra.yaml`; CLI flags override them.

## Environment variables in batch jobs

| Variable | Purpose |
|----------|---------|
| `EZRA_SITE` | Site profile name under `sites/<name>/` |
| `EZRA_MODELS_DIR` | Where weights are stored |
| `EZRA_HOME` | Config / state home |
| `EZRA_ROOT` | Repo checkout path inside the job (optional) |
| `EZRA_WORKERS` | Parallel download workers in download jobs |
| `MODEL` | Gallery name for single-model download / serve |
| `MAX_SIZE` | Used by `scripts/hpc_download_all.sh` (default `14`) |
| `HF_TOKEN` | Hugging Face token for gated repos |
| `EZRA_HOST` / `EZRA_PORT` | Bind for serve jobs (default `0.0.0.0:8000`) |
| `EZRA_HOLD_SECONDS` | How long interactive/serve-placeholder jobs sleep |

Full list: [Configuration](configuration.md).

## Checklist

1. `ezra hpc init-site <name>` and edit `EDIT ME` fields; commit the profile.
2. `export EZRA_SITE=<name>` and set `EZRA_MODELS_DIR` to scratch.
3. `ezra doctor` then `ezra hpc submit download --dry-run`.
4. Submit; check `ezra models status` when the job finishes.
