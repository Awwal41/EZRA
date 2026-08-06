# Models

EZRA ships a curated gallery of free/open checkpoints (general LLMs plus chemistry/materials models). Browse by name, download one or many, then check disk usage.

Gallery source: [`src/ezra/gallery/models.yaml`](../src/ezra/gallery/models.yaml).

## List models

```bash
ezra models list

# search / filter
ezra models list --query qwen
ezra models list --tag chemistry
ezra models list --science
ezra models list --format gguf --max-size 8
ezra models list --no-gated
```

Names marked with `*` are **gated** on Hugging Face (free account + license accept; set `HF_TOKEN`).

## Download

```bash
# one model
ezra models download qwen2.5-7b-instruct

# several
ezra models download chemllm-7b matscibert chembert-uncased

# all free gallery models (skips gated by default)
ezra models download --all

# chemistry / materials subset
ezra models download --all --tag chemistry
ezra models download --all --science

# keep downloads small (laptop smoke test)
ezra models download --all --format gguf --max-size 4 --no-gated

# preview without fetching
ezra models download --all --dry-run
```

Useful flags:

| Flag | Meaning |
|------|---------|
| `--all` | Download every model matching filters |
| `--tag TAG` | With `--all`, only that tag |
| `--science` | With `--all`, only science-tagged models |
| `--format gguf\|safetensors` | Restrict format |
| `--max-size N` | Max size in billions of params |
| `--no-gated` / `--include-gated` | Exclude or include gated HF repos |
| `--workers N` | Parallel downloads (default from config, usually 2) |
| `--force` | Re-download even if already present |
| `--dry-run` | Print what would be fetched |

Weights land under your chosen models directory (see [Install — Where models are stored](install.md)):

```bash
ezra --models-dir /data/ezra/models models download qwen2.5-7b-instruct
# or: export EZRA_MODELS_DIR=/data/ezra/models
```

Default without overrides: `~/.ezra/models/<name>/`.

### Gated models

```bash
export HF_TOKEN=hf_xxx   # Hugging Face access token
# Accept the model license on the HF website for that repo
ezra models download llama-3.1-70b-instruct --include-gated
# or: ezra models download --all --include-gated
```

## Inspect and manage

```bash
ezra models info chemllm-7b
ezra models status
ezra models remove chemllm-7b
ezra models remove chemllm-7b --dry-run
```

## Tips

- Prefer `--dry-run` first on HPC so you know size and count before a long job.
- Use `--max-size` and `--format gguf` when disk or network is limited.
- For bulk staging on a cluster, prefer a SLURM download job — see [HPC](hpc.md).
