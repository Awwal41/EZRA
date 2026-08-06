# Site notes — CUSTOMIZE ME

Fill this in when you add a profile so the next person on the same HPC knows what works.
Then commit this folder and open a PR (no tokens / private secrets).

| Field | Your notes |
|-------|------------|
| Cluster / center name | |
| Typical login host | |
| Recommended scratch / project path | e.g. `$SCRATCH/ezra/models` or `/projects/…` |
| Partition for downloads (CPU) | |
| Partition for GPU serve | |
| Account / allocation flag | `--account=…` |
| GPU GRES example | e.g. `gpu:1` or `gpu:a100:1` |
| Modules that work | python / cuda versions |
| Docs link | center user guide URL |

## Quick start on this cluster

```bash
export EZRA_SITE=<this-folder-name>
export EZRA_MODELS_DIR=…   # your scratch (or set models_dir in ezra.yaml)
# optional: cp .env.example .env && edit HF_TOKEN / EZRA_SITE
ezra doctor
ezra hpc submit download --model qwen2.5-7b-instruct --dry-run
```

## Sharing

```bash
git add sites/<this-folder-name>
git commit -m "Add <cluster> SLURM site profile"
git push
```
