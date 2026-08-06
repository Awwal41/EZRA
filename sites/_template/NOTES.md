# Site notes - EDIT ME

Fill this in when you add a profile so the next person on the same HPC knows what works.

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

## Smoke test

```bash
export EZRA_SITE=<this-folder-name>
export EZRA_MODELS_DIR=…   # your scratch
ezra doctor
ezra hpc submit download --model qwen2.5-7b-instruct --dry-run
```

## Sharing

Commit this folder (yaml + modules.sh + NOTES) and open a PR. Omit tokens and private paths.
