# Peekaboo (macOS screen + UI automation)

EZRA vendors [Peekaboo](https://github.com/openclaw/Peekaboo) as a **git submodule**
under [`third_party/Peekaboo/`](../third_party/Peekaboo/) (MIT). Peekaboo is a
macOS CLI and optional MCP server for screenshots, accessibility inspection, and
UI automation — useful for personal agents that need to *see* the desktop.

Use the [`ezra.peekaboo`](../src/ezra/peekaboo/) adapter from Python and the CLI.
Do not import Peekaboo's Swift/Node tree directly from the rest of EZRA.

## Setup

```bash
# from EZRA repo root
git submodule update --init --recursive third_party/Peekaboo

# install a runnable CLI (pick one)
brew install steipete/tap/peekaboo
# or build from the submodule (macOS 15+, Swift 6.2+, Node 22+):
#   cd third_party/Peekaboo && pnpm install --frozen-lockfile && pnpm run build:cli
```

Optional overrides:

| Variable / config | Meaning |
|-------------------|---------|
| `EZRA_PEEKABOO_ROOT` | Alternate Peekaboo checkout path |
| `EZRA_PEEKABOO_CLI` / `peekaboo.cli` | Absolute path to the `peekaboo` binary |
| `peekaboo.enabled` | `auto` \| `on` \| `off` in `ezra.yaml` |

Check: `ezra doctor` (Peekaboo line) or `ezra peekaboo status`.

## Python API

```python
from ezra.peekaboo import peekaboo_available, capture_screen, mcp_launch_command

if peekaboo_available():
    path = capture_screen()  # ~/.ezra/captures/peekaboo-….png
    print(path)

print(mcp_launch_command())  # argv for MCP clients
```

On Windows/Linux, `peekaboo_available()` is false and capture raises a clear
error (Peekaboo is macOS-only; see community PeekabooWin / PeekabooX ports).

## CLI

```bash
ezra peekaboo status
ezra peekaboo status --json
ezra peekaboo mcp-config          # JSON snippet for Cursor / Claude
ezra peekaboo capture             # screen → ~/.ezra/captures/
ezra peekaboo capture --path /tmp/desk.png
```

## MCP (Cursor / Claude / Codex)

Print a ready-to-paste config:

```bash
ezra peekaboo mcp-config
# or force the published npm package:
ezra peekaboo mcp-config --npx
```

Example (local binary):

```json
{
  "mcpServers": {
    "peekaboo": {
      "command": "/opt/homebrew/bin/peekaboo",
      "args": ["mcp"]
    }
  }
}
```

Grant **Screen Recording** and **Accessibility** when prompted
(`peekaboo permissions status`). Full upstream docs:
[Peekaboo MCP](https://github.com/openclaw/Peekaboo/blob/main/docs/MCP.md).

## Related

- Vendor index: [`third_party/README.md`](../third_party/README.md)
- Document parsing (MegaParse): [parse](parse.md)
