# gogcli (Google Workspace)

EZRA vendors [gogcli](https://github.com/openclaw/gogcli) as a **git submodule**
under [`third_party/gogcli/`](../third_party/gogcli/) (MIT). The CLI binary is
`gog` — one client for Gmail, Calendar, Drive, Docs, Sheets, and related Google
Workspace APIs, with machine-readable output and safety controls for agents.

Use the [`ezra.gog`](../src/ezra/gog/) adapter from Python and the CLI. Do not
import the Go sources directly from the rest of EZRA.

## Setup

```bash
# from EZRA repo root
git submodule update --init third_party/gogcli

# install a runnable CLI (pick one)
brew install openclaw/tap/gogcli          # macOS / Linux
# Windows: download a release binary from GitHub, or build with Go:
#   cd third_party/gogcli && make build
#   # then put ./bin/gog (or dist) on PATH, or set EZRA_GOG_CLI

gog --version
```

Authorize an account (OAuth Desktop client from Google Cloud):

```bash
gog auth credentials set ~/Downloads/client_secret_*.json
gog auth add you@gmail.com --services gmail,calendar,drive
export GOG_ACCOUNT=you@gmail.com
gog auth doctor --check
```

| Variable / config | Meaning |
|-------------------|---------|
| `EZRA_GOG_ROOT` | Alternate gogcli checkout path |
| `EZRA_GOG_CLI` / `gog.cli` | Absolute path to the `gog` binary |
| `GOG_ACCOUNT` / `EZRA_GOG_ACCOUNT` / `gog.account` | Default Google account |
| `gog.enabled` | `auto` \| `on` \| `off` in `ezra.yaml` |

Check: `ezra doctor` (gog line) or `ezra gog status`.

## Python API

```python
from ezra.gog import gog_available, run_gog, mcp_launch_command

if gog_available():
    result = run_gog(
        "gmail", "search", "newer_than:7d", "--max", "5", "--json",
        readonly=True,
    )
    print(result.stdout)

print(mcp_launch_command())  # ['…/gog', 'mcp']
```

## CLI

```bash
ezra gog status
ezra gog status --json
ezra gog mcp-config
# Forward to gog (defaults to --readonly):
ezra gog run gmail search 'newer_than:7d' --max 5 --json
ezra gog run calendar events --today --json
ezra gog run --no-readonly drive ls
```

## MCP (Cursor / Claude / Codex)

```bash
ezra gog mcp-config
```

Example:

```json
{
  "mcpServers": {
    "gog": {
      "command": "gog",
      "args": ["mcp"]
    }
  }
}
```

`gog mcp` is **read-only by default**; writes need explicit authorization.
Upstream guide: [gogcli MCP](https://github.com/openclaw/gogcli/blob/main/docs/mcp.md).

## Related

- Vendor index: [`third_party/README.md`](../third_party/README.md)
- macOS screen capture: [peekaboo](peekaboo.md)
- Upstream: [openclaw/gogcli](https://github.com/openclaw/gogcli)
