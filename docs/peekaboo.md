# Peekaboo (macOS screen + UI automation)

EZRA vendors [Peekaboo](https://github.com/openclaw/Peekaboo) as a **full in-tree
source snapshot** under [`third_party/Peekaboo/`](../third_party/Peekaboo/) (MIT),
including nested dependency trees (AXorcist, Tachikoma, Commander, TauTUI,
Swiftdansi). This is **not** a git submodule — sources ship with EZRA.

Peekaboo is a macOS CLI and optional MCP server for screenshots, accessibility
inspection, and UI automation. Use [`ezra.peekaboo`](../src/ezra/peekaboo/);
do not import the Swift/Node tree from the rest of EZRA.

Pin: see [`third_party/Peekaboo/UPSTREAM.txt`](../third_party/Peekaboo/UPSTREAM.txt).

## Setup

```bash
# sources are already under third_party/Peekaboo/
brew install steipete/tap/peekaboo
# or build from the vendored tree (macOS 15+, Swift 6.2+, Node 22+):
#   cd third_party/Peekaboo && pnpm install --frozen-lockfile && pnpm run build:cli
```

| Variable / config | Meaning |
|-------------------|---------|
| `EZRA_PEEKABOO_ROOT` | Alternate Peekaboo checkout path |
| `EZRA_PEEKABOO_CLI` / `peekaboo.cli` | Absolute path to the `peekaboo` binary |
| `peekaboo.enabled` | `auto` \| `on` \| `off` in `ezra.yaml` |

Check: `ezra doctor` or `ezra peekaboo status`.

## Python API

```python
from ezra.peekaboo import peekaboo_available, capture_screen, mcp_launch_command

if peekaboo_available():
    path = capture_screen()  # ~/.ezra/captures/peekaboo-….png
    print(path)

print(mcp_launch_command())  # argv for MCP clients
```

On Windows/Linux, `peekaboo_available()` is false (macOS-only).

## CLI

```bash
ezra peekaboo status
ezra peekaboo status --json
ezra peekaboo mcp-config
ezra peekaboo capture
```
