# Cline (coding agent)

EZRA vendors [Cline](https://github.com/cline/cline) as a **full in-tree
source snapshot** under [`third_party/Cline/`](../third_party/Cline/) (Apache-2.0).
This is **not** a git submodule: every file is stored in the EZRA repository so
clones keep working even if upstream disappears or stops being open source.

Cline is an autonomous coding agent (CLI, SDK, VS Code extension). EZRA wraps
it with [`ezra.cline`](../src/ezra/cline/) so agents and `ezra doctor` share
one resolution path.

**Safety defaults:** EZRA never auto-runs a Cline agent session, never starts
Kanban, and never installs IDE extensions for you. The tree is pinned to the
commit recorded in [`third_party/Cline/UPSTREAM.txt`](../third_party/Cline/UPSTREAM.txt).

The nested eval harness formerly a git submodule is also vendored as files
under `third_party/Cline/evals/cline-bench/` (not a live gitlink).

## Setup

```bash
# Cline sources are already in the EZRA checkout under third_party/Cline/
# optional: install a global CLI (Node 22+)
npm i -g cline
# or build from the vendored tree — see third_party/Cline/README.md (Bun)
```

| Variable / config | Meaning |
|-------------------|---------|
| `EZRA_CLINE_ROOT` | Alternate Cline checkout path |
| `EZRA_CLINE_CLI` / `cline.cli` | Absolute path to the `cline` binary |
| `cline.enabled` | `auto` \| `on` \| `off` in `ezra.yaml` (shown by doctor/status; does not gate CLI today) |

Check: `ezra doctor` (Cline line) or `ezra cline status`.

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
