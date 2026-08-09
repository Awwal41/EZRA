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

## `ezra agents`

Scaffold personal agents (system prompt + preferred gallery models). See [Personal agents](agents.md) and [agents/README.md](../agents/README.md).

| Command | Description |
|---------|-------------|
| `list` | Profiles under `agents/` (incl. `agents/local/…`) |
| `init NAME` | Copy `agents/_template` → `agents/<NAME>` |
| `show NAME` | Summary + prompt preview (`--prompt` for full text) |
| `check NAME` | Validate aliases vs gallery; suggest downloads |

`init` accepts `--force` and `--description TEXT`. Names may be `my-bot` or `local/my-bot`.

Examples:

```bash
ezra agents init my-lab-assistant
ezra agents init local/scratch-bot --description "Private experiments"
ezra agents list
ezra agents show chem-assistant --prompt
ezra agents check chem-assistant
```

## `ezra openclaw`

Status helpers for the pinned [OpenClaw](https://github.com/openclaw/openclaw) submodule. See [OpenClaw](openclaw.md).

| Command | Description |
|---------|-------------|
| `status` | Submodule / CLI availability (`--json`) |
| `version` | Probe `openclaw --version` if resolvable |

EZRA never auto-runs `onboard` or starts the Gateway.

## `ezra parse`

Parse a document to LLM-ready text (basic backend for notes/text; MegaParse for PDF/Office). See [Document parsing](parse.md).

| Flag | Meaning |
|------|---------|
| `--backend auto\|basic\|megaparse` | Override `parse.backend` |
| `--strategy auto\|fast\|hi_res` | MegaParse strategy |
| `-o` / `--output PATH` | Write result to a file |
| `--json` | Emit JSON with metadata + text |

```bash
ezra parse paper.pdf -o paper.md
ezra parse notes.md
```

## `ezra peekaboo`

macOS Peekaboo helpers (vendored submodule). See [Peekaboo](peekaboo.md).

```bash
ezra peekaboo status
ezra peekaboo status --json
ezra peekaboo mcp-config
ezra peekaboo mcp-config --npx
ezra peekaboo capture [--path PATH] [--mode screen]
```

## `ezra gog`

Google Workspace helpers via gogcli (`gog`). See [gogcli](gog.md).

```bash
ezra gog status
ezra gog status --json
ezra gog mcp-config
ezra gog run gmail search 'newer_than:7d' --json
ezra gog run --no-readonly calendar events --today
```

## `ezra chat`

Interactive (or one-shot) chat with a gallery model or personal agent. Requires `pip install -e ".[local]"` for real GGUF replies (or `--backend stub` to dry-run).

| Flag | Meaning |
|------|---------|
| `--agent NAME` | Bind `agents/<name>/` (prompt + preferred models) |
| `--model NAME` | Gallery alias |
| `--backend auto\|llama\|mlx\|stub` | Inference backend (default `auto`) |
| `-p` / `--prompt TEXT` | One-shot non-interactive prompt |
| `--file PATH` | Parse a document and prepend it to the first message |
| `--stream` / `--no-stream` | Token streaming in the REPL |

REPL commands: `/save` (write `~/.ezra/sessions/<id>.json`), `/quit`.

```bash
ezra chat --model qwen2.5-7b-instruct
ezra chat --agent chem-assistant
ezra chat --backend stub --model phi-3.5-mini-instruct -p "Hello"
ezra chat --file paper.pdf --model qwen2.5-7b-instruct -p "Summarize methods"
```

## `ezra serve`

OpenAI-compatible HTTP API (`GET /v1/models`, `POST /v1/chat/completions`). Requires `pip install -e ".[serve]"` plus a local backend extra.

| Flag | Meaning |
|------|---------|
| `--agent` / `--model` | Default binding for the process |
| `--backend` | `auto` / `llama` / `mlx` / `stub` |
| `--host` / `--port` | Bind address (defaults `0.0.0.0:8000`, or `EZRA_HOST` / `EZRA_PORT`) |

Request `model` may be a gallery alias or `agent:<name>`. Responses include `ezra.agent`, `ezra.backend`, and `ezra.resolved_model`.

```bash
ezra serve --model qwen2.5-7b-instruct --port 8000
ezra serve --agent chem-assistant --backend stub
```

See [Conversation runtime](conversation.md).

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

More detail: [Models](models.md), [Personal agents](agents.md), [HPC](hpc.md).
