# Cline (coding agent)

EZRA vendors [Cline](https://github.com/cline/cline) as a **full in-tree
source snapshot** under [`third_party/Cline/`](../third_party/Cline/) (Apache-2.0).
This is **not** a git submodule: every file is stored in the EZRA repository so
clones keep working even if upstream disappears or stops being open source.

Cline is an autonomous coding agent (CLI, SDK, VS Code extension). EZRA wraps
it with [`ezra.cline`](../src/ezra/cline/) so agents and `ezra doctor` share
one resolution path. To use Cline **from the IDE** without the marketplace,
sideload [EZRA Grid](ide.md) and pick the Cline lane (`ezra ide install`).

**Safety defaults:** EZRA never auto-runs a Cline agent session, never starts
Kanban, and never installs IDE extensions for you. The tree is pinned to the
commit recorded in [`third_party/Cline/UPSTREAM.txt`](../third_party/Cline/UPSTREAM.txt).

The nested eval harness formerly a git submodule is also vendored as files
under `third_party/Cline/evals/cline-bench/` (not a live gitlink).

## Setup

Cline is **optional**. Grid **Local** / **Agent** and `ezra chat` / `ezra serve`
do not use it. Only the **Cline** lane (and `ezra cline …` / a shell `cline`
command) needs a CLI. Full recipe and skip-vs-install table:
[Cline + a free EZRA model](cline-local.md#local-chat-vs-the-cline-cli).

EZRA resolves a CLI in this order:

1. `EZRA_CLINE_CLI` / `cline.cli`
2. `cline` on `PATH` (for example `npm i -g cline`)
3. Built `third_party/Cline/apps/cli/dist/index.js` (Node)
4. Source `third_party/Cline/apps/cli/src/index.ts` (needs Bun 1.3+)

```bash
# Cline sources are already in the EZRA checkout under third_party/Cline/
# pick ONE if you want the coding agent:
npm i -g cline                          # Node 22+ — simplest on Windows
# bun from https://bun.sh               # runs the vendored .ts entry
# or build dist/index.js — see third_party/Cline/README.md
# or: export EZRA_CLINE_CLI=/path/to/cline
```

| Variable / config | Meaning |
|-------------------|---------|
| `EZRA_CLINE_ROOT` | Alternate Cline checkout path |
| `EZRA_CLINE_CLI` / `cline.cli` | Absolute path to the `cline` binary |
| `cline.enabled` | `auto` \| `on` \| `off` in `ezra.yaml` (shown by doctor/status; does not gate CLI today) |

Check: `ezra doctor` (Cline line) or `ezra cline status`.

## Off-grid: EZRA models, no cloud API key

Cline normally wants Anthropic, OpenRouter, a Cline account, or similar. **You
do not have to.** Point Cline at EZRA’s OpenAI-compatible server so it uses
gallery weights you already downloaded:

```bash
pip install -e ".[local,serve]"
ezra models download qwen2.5-7b-instruct

# keep running
ezra serve --model qwen2.5-7b-instruct --host 127.0.0.1 --port 8000

# once: save Cline provider settings (does not start an agent)
ezra cline use-local --model qwen2.5-7b-instruct --auth
```

`ezra-local` is a dummy key string Cline’s `openai-compatible` provider
requires. EZRA serve does not validate it. Then:

```bash
cline -P openai-compatible -k ezra-local -m qwen2.5-7b-instruct "your task"
```

Or pick the **Cline** lane in [EZRA Grid](ide.md). Full recipe (download a free
GGUF → serve → Cline → VS Code / Cursor): [Cline + a free EZRA model](cline-local.md).

## Python API

```python
from ezra.cline import cline_available, cline_root, resolve_cli

if cline_available():
    print(cline_root())   # …/third_party/Cline
    print(resolve_cli())
```

To invoke the CLI explicitly (you choose the args):

```python
from ezra.cline import run_cline

run_cline("--version")  # safe probe
# Do not start an agent session from library code unless the user asked.
```

## CLI

```bash
ezra cline status
ezra cline status --json
ezra cline version
ezra cline use-local [--model NAME] [--auth]
```

## Security notes

Cline can edit files, run shell commands, and talk to model providers. Before
enabling it:

1. Read upstream [SECURITY.md](../third_party/Cline/SECURITY.md) in the vendored tree
2. Prefer local / approval-gated configs; do not auto-approve destructive tools
3. Keep EZRA’s adapter as the only entry point from Python

## Refreshing the snapshot

When you deliberately upgrade Cline:

```bash
# from a scratch dir
git clone --depth 1 https://github.com/cline/cline.git /tmp/cline
git -C /tmp/cline submodule update --init --depth 1
rm -rf third_party/Cline
mkdir third_party/Cline
# copy sources (no .git), keep LICENSE
# update third_party/Cline/UPSTREAM.txt with the new commit/date
git add third_party/Cline
```

Do **not** turn this path back into a submodule.
