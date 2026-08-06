# Site profiles (per-HPC customization)

Every cluster is different: partition names, accounts, `module load` lines, GPU GRES strings, and scratch paths. **EZRA expects you to customize for your machine** - do not assume the generic `scripts/hpc_*.sh` defaults match your site.

## Quick start (your cluster)

```bash
# from the repo root, after pip install -e .
ezra hpc init-site my-cluster --models-dir /scratch/$USER/ezra/models

# edit the generated files (look for "EDIT ME")
$EDITOR sites/my-cluster/ezra.yaml
$EDITOR sites/my-cluster/modules.sh
$EDITOR sites/my-cluster/NOTES.md
```

Then use the profile:

```bash
export EZRA_SITE=my-cluster
# EZRA_MODELS_DIR still overrides yaml if you set it:
# export EZRA_MODELS_DIR=/scratch/$USER/ezra/models

ezra doctor
ezra hpc submit download --models-dir /scratch/$USER/ezra/models --dry-run
ezra hpc submit download
```

`EZRA_SITE` makes batch scripts and `ezra hpc` load:

| File | Used for |
|------|----------|
| `sites/$EZRA_SITE/ezra.yaml` | SLURM defaults (`partition`, `account`, CPUs, GPUs, …) via `EZRA_CONFIG` |
| `sites/$EZRA_SITE/modules.sh` | `module load` / env setup inside SBATCH jobs |

## What you should edit

In **`ezra.yaml`** (search for `EDIT ME`):

- `hpc.slurm.partition` / `account` / `qos` / `constraint`
- Per-job `cpus`, `mem`, `gpus`, `time`, optional `gres` (e.g. `gpu:a100:1`)
- `local.models_dir` (or pass `--models-dir` to `init-site` / use `EZRA_MODELS_DIR`)

In **`modules.sh`** (search for `EDIT ME`):

- `module load python/…`
- `module load cuda/…` (GPU jobs)
- Any site compiler / MPI modules your admins require

In **`NOTES.md`**:

- Cluster name, how to request an allocation, scratch path convention, links to your center’s docs

## Commit and push (so others on the same HPC benefit)

Site profiles **without secrets** belong in git:

```bash
git checkout -b sites/my-cluster
git add sites/my-cluster
git commit -m "Add my-cluster SLURM site profile (partition, modules, notes)"
git push -u origin sites/my-cluster
# open a PR against awwalola/EZRA
```

**Do not commit:**

- `HF_TOKEN`, passwords, or private account numbers you are not allowed to share
- Absolute paths to your personal home if they contain usernames you want private (prefer `$SCRATCH` / `$USER` in NOTES instead)
- Model weights

Personal-only overrides can live in `~/.ezra/ezra.yaml` or `export EZRA_CONFIG=…` and stay untracked.

## Layout

```text
sites/
  README.md          ← this file
  _template/         ← copied by `ezra hpc init-site`
    ezra.yaml
    modules.sh
    NOTES.md
  my-cluster/        ← your committed profile (example name)
    …
```

Generic example scripts under `scripts/hpc_*.sh` remain; prefer generating or submitting with `EZRA_SITE` set so your profile applies automatically.
