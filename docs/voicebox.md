# Voicebox (AI voice studio)

EZRA vendors [Voicebox](https://github.com/jamiepine/voicebox) as a **full in-tree
source snapshot** under [`third_party/Voicebox/`](../third_party/Voicebox/) (MIT).
This is **not** a git submodule: every file is stored in the EZRA repository so
clones keep working even if upstream disappears or stops being open source.

Voicebox is a local-first AI voice studio (clone, TTS, dictation, MCP agent
voice). EZRA wraps it with [`ezra.voicebox`](../src/ezra/voicebox/) so agents and
`ezra doctor` share one resolution path for the vendored tree and MCP config.

**Safety defaults:** EZRA never auto-starts the Voicebox app, never downloads
TTS/STT models for you, and never installs MCP clients. The tree is pinned to
the commit recorded in
[`third_party/Voicebox/UPSTREAM.txt`](../third_party/Voicebox/UPSTREAM.txt).

## Setup

Voicebox is **optional**. Start the desktop app (or `just dev` in the vendored
tree) yourself when you want agent voice I/O. Default local API/MCP port is
**17493**.

```bash
# sources are already under third_party/Voicebox/
# pick ONE to run Voicebox:
#   install a release from https://voicebox.sh
#   or: cd third_party/Voicebox && just setup && just dev
```

| Variable / config | Meaning |
|-------------------|---------|
| `EZRA_VOICEBOX_ROOT` | Alternate Voicebox checkout path |
| `EZRA_VOICEBOX_URL` / `voicebox.url` | Base HTTP URL (default `http://127.0.0.1:17493`) |
| `EZRA_VOICEBOX_CLIENT_ID` / `voicebox.client_id` | `X-Voicebox-Client-Id` (default `ezra`) |
| `EZRA_VOICEBOX_MCP` | Absolute path to `voicebox-mcp` stdio shim |
| `voicebox.enabled` | `auto` \| `on` \| `off` in `ezra.yaml` (shown by doctor/status) |

Check: `ezra doctor` (Voicebox line) or `ezra voicebox status`.

## MCP (Cursor / Claude / Cline)

With Voicebox running, paste the HTTP MCP snippet:

```bash
ezra voicebox mcp-config
# or: ezra voicebox mcp-config --client-id cursor
```

Typical shape:

```json
{
  "mcpServers": {
    "voicebox": {
      "url": "http://127.0.0.1:17493/mcp",
      "headers": { "X-Voicebox-Client-Id": "ezra" }
    }
  }
}
```

Stdio fallback (when a `voicebox-mcp` shim is built/installed):

```bash
ezra voicebox mcp-config --stdio
```

Tools exposed by upstream: `voicebox.speak`, `voicebox.transcribe`,
`voicebox.list_captures`, `voicebox.list_profiles`.

## Python API

```python
from ezra.voicebox import voicebox_available, voicebox_root, mcp_http_config, probe_server

if voicebox_available():
    print(voicebox_root())      # …/third_party/Voicebox
    print(mcp_http_config())    # Cursor MCP snippet
    print(probe_server())       # only if the app is already running
```

## CLI

```bash
ezra voicebox status
ezra voicebox status --json
ezra voicebox mcp-config [--client-id NAME] [--stdio]
ezra voicebox health [--json]
```

## Security notes

Voicebox can speak aloud, transcribe audio, and accept MCP tool calls from any
local client that can reach port 17493. Before enabling it:

1. Read upstream [SECURITY.md](../third_party/Voicebox/SECURITY.md) and
   [RESPONSIBLE_USE.md](../third_party/Voicebox/RESPONSIBLE_USE.md)
2. Keep the backend bound to localhost; do not expose `/mcp` on a public interface
3. Prefer this adapter for path / MCP snippets — do not scrape the vendor tree from agents

## Refreshing the snapshot

When you deliberately upgrade Voicebox:

```bash
# from a scratch dir
git clone --depth 1 https://github.com/jamiepine/voicebox.git /tmp/voicebox
rm -rf third_party/Voicebox
mkdir third_party/Voicebox
# copy sources (no .git), keep LICENSE
# update third_party/Voicebox/UPSTREAM.txt with the new commit/date
git add third_party/Voicebox
```

Do **not** turn this path back into a submodule.
