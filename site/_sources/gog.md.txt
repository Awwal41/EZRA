# gogcli (Google Workspace)

EZRA vendors [gogcli](https://github.com/openclaw/gogcli) as a **full in-tree
source snapshot** under [`third_party/gogcli/`](../third_party/gogcli/) (MIT).
This is **not** a git submodule — sources ship with EZRA.

The CLI binary is `gog` — Gmail, Calendar, Drive, Docs, Sheets, and related
Google Workspace APIs, with machine-readable output for agents. Use
[`ezra.gog`](../src/ezra/gog/); do not import the Go sources from the rest of EZRA.

Pin: see [`third_party/gogcli/UPSTREAM.txt`](../third_party/gogcli/UPSTREAM.txt).

## Setup

```bash
# sources are already under third_party/gogcli/
brew install openclaw/tap/gogcli          # macOS / Linux
# Windows: download a release binary, or build:
#   cd third_party/gogcli && make build
#   # then put ./bin/gog on PATH, or set EZRA_GOG_CLI

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
| `EZRA_GOG_ROOT` | Alternate gogcli checkout |
| `EZRA_GOG_CLI` / `gog.cli` | Path to `gog` binary |
| `GOG_ACCOUNT` / `EZRA_GOG_ACCOUNT` / `gog.account` | Default account |
| `gog.enabled` | `auto` \| `on` \| `off` (shown by doctor/status; does not gate CLI today) |

Check: `ezra doctor` or `ezra gog status`.

## Python API

```python
from ezra.gog import gog_available, run_gog, mcp_launch_command

if gog_available():
    run_gog("--readonly", "gmail", "search", "newer_than:7d", "--json")
```

## CLI

```bash
ezra gog status
ezra gog mcp-config
ezra gog run gmail search 'newer_than:7d' --max 5 --json
```

`ezra gog run` defaults to `--readonly` for safer agent use.
