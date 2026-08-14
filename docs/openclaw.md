# OpenClaw (personal AI gateway)

EZRA vendors [OpenClaw](https://github.com/openclaw/openclaw) as a **full in-tree
source snapshot** under [`third_party/OpenClaw/`](../third_party/OpenClaw/) (MIT).
This is **not** a git submodule: every file is stored in the EZRA repository so
clones keep working even if upstream disappears or stops being open source.

OpenClaw is a multi-channel personal AI assistant / Gateway (TypeScript, Node).
EZRA wraps it with [`ezra.openclaw`](../src/ezra/openclaw/) so agents and
`ezra doctor` share one resolution path. To use OpenClaw **from the IDE**
without a marketplace, sideload [EZRA Grid](ide.md) and pick the OpenClaw lane.

**Safety defaults:** EZRA never auto-runs `openclaw onboard`, never installs a
daemon, and never starts the Gateway for you. The tree is pinned to the release
recorded in [`third_party/OpenClaw/UPSTREAM.txt`](../third_party/OpenClaw/UPSTREAM.txt).

## Setup

```bash
# OpenClaw sources are already in the EZRA checkout under third_party/OpenClaw/
# optional: install a global CLI (Node 22+)
npm install -g openclaw@latest
# or build from the vendored tree — see third_party/OpenClaw/README.md (pnpm)
```

| Variable / config | Meaning |
|-------------------|---------|
| `EZRA_OPENCLAW_ROOT` | Alternate OpenClaw checkout path |
| `EZRA_OPENCLAW_CLI` / `openclaw.cli` | Absolute path to the `openclaw` binary |
| `openclaw.enabled` | `auto` \| `on` \| `off` in `ezra.yaml` (shown by doctor/status; does not gate CLI today) |

Check: `ezra doctor` (OpenClaw line) or `ezra openclaw status`.

## Python API

```python
from ezra.openclaw import openclaw_available, openclaw_root, resolve_cli

if openclaw_available():
    print(openclaw_root())   # …/third_party/OpenClaw
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

1. Read upstream [SECURITY.md](https://github.com/openclaw/openclaw/blob/main/SECURITY.md) (also in the vendored tree)
2. Prefer local / sandbox configs; do not expose the Gateway publicly
3. Keep EZRA’s adapter as the only entry point from Python

## Refreshing the snapshot

When you deliberately upgrade OpenClaw:

```bash
# from a scratch dir
git clone --depth 1 --branch <tag> https://github.com/openclaw/openclaw.git /tmp/openclaw
rm -rf third_party/OpenClaw
mkdir third_party/OpenClaw
# copy sources (no .git), keep LICENSE / THIRD_PARTY_NOTICES.md
# update third_party/OpenClaw/UPSTREAM.txt with the new tag/date
git add third_party/OpenClaw
```

Do **not** turn this path back into a submodule.
