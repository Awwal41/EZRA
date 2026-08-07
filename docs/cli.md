# CLI reference

```text
ezra [--config PATH] [--models-dir PATH] COMMAND ...
```

Global options:

| Option | Meaning |
|--------|---------|
| `--config PATH` | Path to `ezra.yaml` |
| `--models-dir PATH` | Override model storage directory |
| `--version` | Print version |

## `ezra doctor`

Environment check: version, models dir, HF token, gallery size, CPU/RAM/GPU fit budget, write test. Mentions `ezra models recommend` for hardware-aware picks.

## `ezra init-config`

Copy `ezra.yaml.example` (or packaged defaults) so you can customize paths locally:

| Flag | Effect |
|------|--------|
| (default) / `--home` | Write `~/.ezra/ezra.yaml` |
| `--cwd` | Write `./ezra.yaml` (gitignored at repo root) |
| `--env` | Also copy `.env.example` → `.env` |
| `--force` | Overwrite if the target already exists |

For HPC partition / modules, use `ezra hpc init-site` instead. See [Configuration](configuration.md).

## `ezra models`

| Command | Description |
|---------|-------------|
| `list` | Browse the gallery |
| `recommend [KEYWORD]` | Rank open models that fit this machine |
| `download NAME [NAME …]` | Download named models |
| `download --all` | Download matching free models |
| `info NAME` | Details for one model |
| `status` | Installed models and disk usage |
| `remove NAME [NAME …]` | Delete installed model directories |

### `models list` flags

`--query`, `--tag`, `--science`, `--format`, `--max-size`, `--include-gated` / `--no-gated`, `--json`

### `models recommend` flags

`KEYWORD` (optional), `--limit`, `--tag`, `--science`, `--format`, `--include-gated` / `--no-gated`, `--json`

Examples: `ezra models recommend chemistry`, `ezra models recommend --format gguf`. Full guide: [Models - Recommend](models.md#recommend-for-this-machine).

### `models download` flags

`--all`, `--tag`, `--science`, `--format`, `--max-size`, `--include-gated` / `--no-gated`, `--quant`, `--force`, `--dry-run`, `--workers`, `--json`

## `ezra hpc`

| Command | Description |
|---------|-------------|
| `templates` | List job kinds and default resources |
| `sites` | List committed profiles under `sites/` |
| `init-site NAME` | Copy `sites/_template` → `sites/<NAME>` (then edit & push) |
| `script KIND` | Print or write an SBATCH script |
| `submit KIND` | Generate script and run `sbatch` |

`KIND` is one of: `download`, `serve`, `interactive`.

Shared resource flags: `--models-dir`, `--time`, `--cpus`, `--mem`, `--gpus`, `--gres`, `--partition`, `--account`, `--qos`, `--constraint`, `--job-name`.

`submit` also accepts `--model`, `--dry-run`, and repeatable `--sbatch-arg`.

`init-site` accepts `--models-dir PATH` to write `local.models_dir` into the new profile.

Set `EZRA_SITE=<name>` after `init-site` so config/modules match your cluster. See [sites/README.md](sites.md).

Examples:

```bash
ezra hpc init-site my-cluster --models-dir /scratch/$USER/ezra/models
export EZRA_SITE=my-cluster
ezra hpc templates
ezra hpc sites
ezra hpc script download --models-dir /scratch/$USER/ezra/models -o /tmp/ezra-dl.sh
ezra hpc submit download --models-dir /scratch/$USER/ezra/models --dry-run
ezra hpc submit serve --model chemllm-7b --gpus 1 --mem 64G
```

More detail: [Models](models.md), [HPC](hpc.md).
