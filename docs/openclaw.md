# OpenClaw (personal AI gateway)

EZRA vendors [OpenClaw](https://github.com/openclaw/openclaw) as a **git submodule**
under [`third_party/OpenClaw/`](../third_party/OpenClaw/) (MIT). OpenClaw is a
multi-channel personal AI assistant / Gateway (TypeScript, Node). EZRA wraps it
with [`ezra.openclaw`](../src/ezra/openclaw/) so agents and `ezra doctor` share
one resolution path.

**Safety defaults:** EZRA never auto-runs `openclaw onboard`, never installs a
daemon, and never starts the Gateway for you. Submodule checkout is
**shallow** and **pinned** to a release tag (not floating `main`).

## Setup

```bash
# from EZRA repo root
git submodule update --init --depth 1 third_party/OpenClaw

# optional: install a global CLI (Node 22+)
npm install -g openclaw@latest
# or build from the submodule — see upstream README (pnpm workspace)
```

| Variable / config | Meaning |
|-------------------|---------|
| `EZRA_OPENCLAW_ROOT` | Alternate OpenClaw checkout path |
| `EZRA_OPENCLAW_CLI` / `openclaw.cli` | Absolute path to the `openclaw` binary |
| `openclaw.enabled` | `auto` \| `on` \| `off` in `ezra.yaml` |

Check: `ezra doctor` (OpenClaw line) or `ezra openclaw status`.

## Python API

```python
from ezra.openclaw import openclaw_available, openclaw_root, resolve_cli

if openclaw_available():
    print(openclaw_root())
    print(resolve_cli())
```

To invoke the CLI explicitly (you choose the args):

```python
from ezra.openclaw import run_openclaw

run_openclaw("--version")  # safe probe
# Do not call onboard / gateway start from library code unless the user asked.
```

## CLI

```bash
ezra openclaw status
ezra openclaw status --json
ezra openclaw version
```

## Security notes

OpenClaw can connect messaging channels and run host tools. Before enabling it:

1. Read upstream [SECURITY.md](https://github.com/openclaw/openclaw/blob/main/SECURITY.md)
2. Prefer local / sandbox configs; do not expose the Gateway publicly
3. Keep EZRA’s adapter as the only entry point from Python

## Updating the pin

```bash
cd third_party/OpenClaw
git fetch --depth 1 origin tag vYYYY.M.P
git checkout --detach FETCH_HEAD
cd ../..
git add third_party/OpenClaw
# update the pin note in third_party/README.md, then commit
```

Do **not** track upstream `main` tip without review — the repo is large and
moves quickly.
