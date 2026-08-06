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

Environment check: version, models dir, HF token, gallery size, write test.

## `ezra models`

| Command | Description |
|---------|-------------|
| `list` | Browse the gallery |
| `download NAME [NAME …]` | Download named models |
| `download --all` | Download matching free models |
| `info NAME` | Details for one model |
| `status` | Installed models and disk usage |
| `remove NAME [NAME …]` | Delete installed model directories |

### `models list` flags

`--query`, `--tag`, `--science`, `--format`, `--max-size`, `--include-gated` / `--no-gated`, `--json`

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

Shared resource flags: `--time`, `--cpus`, `--mem`, `--gpus`, `--gres`, `--partition`, `--account`, `--qos`, `--constraint`, `--job-name`.

`submit` also accepts `--model`, `--dry-run`, and repeatable `--sbatch-arg`.

Set `EZRA_SITE=<name>` after `init-site` so config/modules match your cluster. See [sites/README.md](../sites/README.md).

Examples:

```bash
ezra hpc init-site my-cluster
export EZRA_SITE=my-cluster
ezra hpc templates
ezra hpc sites
ezra hpc script download -o /tmp/ezra-dl.sh
ezra hpc submit download --dry-run
ezra hpc submit serve --model chemllm-7b --gpus 1 --mem 64G
```

More detail: [Models](models.md), [HPC](hpc.md).
