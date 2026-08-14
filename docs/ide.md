# EZRA Grid (VS Code / Cursor)

Sideload an **off-grid switchboard** into VS Code or Cursor. You pick a
**lane** — EZRA local models, a personal agent, Cline, or OpenClaw — without
publishing anything to a marketplace.

**You do not need a cloud API key** for EZRA local, personal agents, or Cline
when Cline is pointed at `ezra serve`. Those paths use **open models you already
downloaded** with `ezra models download`. A Hugging Face token is only for
*gated* gallery downloads, not for chatting.

The extension sources live at [`ide/vscode/`](../ide/vscode/). EZRA packages a
`.vsix` with the Python stdlib zipper (no `vsce`, no npm) and installs it with
the editor CLI, or by copying into the extensions folder.

**First time on this computer?** Use [Getting started](getting-started.md)
(which wheel to install, then these Grid steps).

**Safety defaults:** EZRA never auto-installs the extension, never auto-starts
Cline, and never starts the OpenClaw Gateway. Cline / OpenClaw only run when
you select that lane and send.

## How to use it

### 1. Sideload (once per machine)

From the EZRA checkout, venv active:

```bash
ezra ide install                 # Cursor and/or VS Code found on this PC
ezra ide install --ide code      # Visual Studio Code only
ezra ide install --ide cursor    # Cursor only
```

`--ide code` installs into **Visual Studio Code**, not Cursor. Open the VS Code
app to chat there.

### 2. Open the Grid and chat (VS Code)

EZRA does **not** add a Copilot / Chat bubble. There is no entry under
**Chat** or the marketplace. Chat lives in the **EZRA Grid** sidebar.

1. In **Visual Studio Code**, press **Ctrl+Shift+P** (macOS: **Cmd+Shift+P**).
2. Run **Developer: Reload Window**. Sideloaded extensions only appear after a reload.
3. Open the Grid with any of these:
   - **Command Palette → `EZRA: Open Grid`** (most reliable)
   - Far-left **activity bar**: four **rising columns** (often near the bottom). Hover until the tooltip says **EZRA Grid**
   - Bottom **status bar**: click **EZRA**
   - **View → Open View…** → type `Grid`
   - Right-click an empty spot on the activity bar and enable **EZRA Grid** if it was hidden
4. Confirm **Extensions** (**Ctrl+Shift+X**) lists **EZRA Grid** as installed. It will not appear in the VS Marketplace search.

In the Grid panel:

1. Click **Local** (plain chat) or **Agent**.
2. Choose a downloaded model from the **Model** dropdown. If it says `(none)`, download one first (next section) and click **Refresh**.
3. Type in the box at the bottom (`Ctrl+Enter to send on the selected lane`).
4. Press **Ctrl+Enter** (macOS: **Cmd+Enter**) or click **Send**. Replies appear in the log above the box.

If the panel says `ezra CLI not found`, set **EZRA Grid → `ezra.pythonPath`** to
the Python that has EZRA installed:

- venv (Windows): `C:\Users\you\EZRA\.venv\Scripts\python.exe`
- Anaconda (Windows): `C:\Users\you\AppData\Local\anaconda3\python.exe`
- or set **`ezra.cliPath`** to the `ezra` executable.

| Looking here | What to use instead |
|--------------|---------------------|
| VS Code **Chat** / Copilot | **EZRA: Open Grid** |
| Cursor (this window) after `--ide code` | Open **Visual Studio Code**, or also run `ezra ide install --ide cursor` |
| Marketplace “EZRA” search | Sideload only — check **Installed** extensions |

### 3. Get a local model (once)

```bash
pip install -r requirements-ide-cpu.txt   # or cuda124 / macos — see docs/getting-started.md
ezra models download qwen2.5-7b-instruct
```

No Anthropic / OpenAI / OpenRouter key. Free/open gallery GGUFs download
without `HF_TOKEN`; gated repos still need a Hugging Face token to *fetch*,
then they run locally.

### 4. Pick a lane and send

| Lane | API key? | What send does |
|------|----------|----------------|
| **EZRA local** | No | `ezra chat` on the GGUF you select in the Grid |
| **Agent** | No | Same, plus `agents/<name>/` system prompt |
| **Cline** | **No, if you use EZRA models** | Terminal hand-off to a **Cline CLI** (not embedded). Skip this lane if you only want chat. |
| **OpenClaw** | Depends on OpenClaw config | Terminal hand-off; EZRA never starts the Gateway |

Type in the composer, **Ctrl+Enter** (or **Cmd+Enter**) to send. **Refresh**
re-reads `ezra ide probe` (installed models, agents, Cline/OpenClaw CLI).

#### EZRA local / Agent (simplest off-grid)

1. Select **Local** (or **Agent** and an `agents/` profile).
2. Choose a downloaded model (local lane).
3. Send. Replies come from llama.cpp / MLX on this machine.

`stub` backend (Settings → `ezra.backend`) dry-runs without weights.

#### Cline on EZRA models (no cloud key)

Cline’s *default* is a paid cloud provider. **Do not do that** unless you want
to. Cookbook with a concrete free GGUF (`phi-3.5-mini-instruct`) through VS Code
or Cursor: [Cline + a free EZRA model](cline-local.md).

EZRA already serves your downloads as OpenAI `/v1`:

```bash
# terminal A — keep this running
ezra serve --model qwen2.5-7b-instruct --host 127.0.0.1 --port 8000

# terminal B — save Cline’s provider once (does not start an agent)
ezra cline use-local --model qwen2.5-7b-instruct --auth
```

`use-local` prints the exact commands. `--auth` writes Cline’s
`openai-compatible` settings to `http://127.0.0.1:8000/v1`. The “API key”
`ezra-local` is a **placeholder** Cline requires; EZRA serve does not check it
and it is not a cloud secret.

Then in the Grid: **Cline** lane → pick the same model → send. A terminal opens
with:

```text
cline -P openai-compatible -k ezra-local -m qwen2.5-7b-instruct "your task"
```

Confirm that line. Cline still asks before editing files / running tools.

A `cline` CLI is required **only** for this lane. Skip it for **Local** /
**Agent**. If `ezra cline status` has no runnable CLI, pick one of:
`npm i -g cline` (Node 22+), Bun 1.3+ for the vendored `.ts`, a vendored
`dist/index.js` build, or `EZRA_CLINE_CLI` — [Cline + free model](cline-local.md#how-to-get-a-cline-cli-pick-one)
and [Cline](cline.md).

#### OpenClaw

OpenClaw is a Gateway, not EZRA chat. The Grid only opens a terminal; it does
**not** run `openclaw onboard` or start the Gateway. You can still point
OpenClaw at the same `http://127.0.0.1:8000/v1` URL if you configure an
OpenAI-compatible model there. See [OpenClaw](openclaw.md).

## Install details

```bash
ezra ide status                 # sources + detected Cursor / VS Code
ezra ide package                # ide/vscode/dist/ezra-grid-*.vsix
ezra ide install                # every detected editor
ezra ide install --ide cursor
ezra ide install --ide code
ezra ide install --dry-run
```

Reload the editor window, then **EZRA: Open Grid** (or the rising-columns
activity-bar icon). See [Open the Grid and chat](#2-open-the-grid-and-chat-vs-code).

Hand-install a VSIX:

```bash
cursor --install-extension ide/vscode/dist/ezra-grid-0.1.0.vsix
code --install-extension ide/vscode/dist/ezra-grid-0.1.0.vsix
```

If the `cursor` / `code` CLI is missing, `ezra ide install` copies into
`~/.cursor/extensions/` or `~/.vscode/extensions/` (Windows: `%USERPROFILE%`).

**Do not** publish this extension to the VS Marketplace or Open VSX.
`package.json` is `"private": true` on purpose.

## Settings

| Setting | Meaning |
|---------|---------|
| `ezra.cliPath` | Absolute path to the `ezra` executable. Empty = look on PATH, then `python -m ezra`. |
| `ezra.pythonPath` | Python used for `python -m ezra` when `ezra` is not on PATH |
| `ezra.defaultLane` | `local` \| `agent` \| `cline` \| `openclaw` |
| `ezra.model` | Gallery alias for local / Cline lanes |
| `ezra.agent` | Personal agent name |
| `ezra.backend` | `auto` \| `llama` \| `mlx` \| `stub` |

## CLI

```bash
ezra ide status
ezra ide status --json
ezra ide probe --json
ezra ide package [-o PATH]
ezra ide install [--ide auto|cursor|code|code-insiders]
ezra ide uninstall
ezra cline use-local [--model NAME] [--auth]
```

| Variable / config | Meaning |
|-------------------|---------|
| `ide.enabled` | `auto` \| `on` \| `off` in `ezra.yaml` (doctor/status only; does not auto-install) |

Uninstall: `ezra ide uninstall`, or the editor’s Extensions view.

## Python API

```python
from ezra.ide import extension_root, package_vsix, probe_grid, install_vsix
from ezra.cline import local_provider_plan

print(extension_root())     # …/ide/vscode
print(local_provider_plan()["base_url"])  # http://127.0.0.1:8000/v1
print(probe_grid()["lanes"]["cline"]["needs_cloud_key"])  # False
```

## Why this is not “the Cline extension”

Cline already ships a full VS Code app under `third_party/Cline/apps/vscode/`.
EZRA Grid does **not** wrap or republish that. It is a small switchboard: EZRA
local inference and personal agents stay in-process via `ezra chat`; Cline is
an explicit terminal hand-off **using your EZRA downloads** through `ezra serve`.
