# Cline + a free EZRA model in VS Code / Cursor

This is the practical recipe: **download one free gallery GGUF**, serve it
locally, point **Cline** at it (no Anthropic / OpenRouter / Cline-account key),
then use it from **VS Code or Cursor** through the sideloaded **EZRA Grid**.

Nothing is published to a marketplace. Weights stay on your disk.

```text
  VS Code / Cursor
        │  EZRA Grid  (Cline lane)
        ▼
     cline CLI   ──openai-compatible──►  ezra serve  (/v1)
                                              │
                                              ▼
                                    ~/.ezra/models/<name>/
                                    (free GGUF you downloaded)
```

Related: [Getting started](getting-started.md) · [Cline facade](cline.md) ·
[EZRA Grid](ide.md) · [Models](models.md) · [Conversation / serve](conversation.md).

---

## What you need

| Piece | Why |
|-------|-----|
| EZRA checkout + venv | `ezra` CLI, gallery, serve — [which wheel](getting-started.md#3-install-ezra-and-the-right-wheel) |
| A **free GGUF** from the gallery | The actual model Cline (or Local chat) will call |
| `pip install -e ".[local,serve]"` | llama.cpp + OpenAI HTTP (prefer a [wheel file](getting-started.md#3-install-ezra-and-the-right-wheel) on Windows) |
| Cline CLI — **Cline lane only** | Coding agent. Skip this if you only want Grid **Local** chat. |
| VS Code or Cursor | Where Grid lives |

No cloud API key. `HF_TOKEN` is only if you pick a **gated** gallery entry
(Meta/Google license click-through). The models in this guide are **not gated**.

### Local chat vs the Cline CLI

Grid does **not** embed Cline. The **Cline** lane always opens a terminal and
runs a `cline` program. `npm i -g cline` is one way to put that program on
PATH. You are **not** stuck with it for everything else.

| What you use | Needs a `cline` CLI? |
|--------------|----------------------|
| Grid **Local** lane | No — `ezra chat` on the GGUF |
| Grid **Agent** lane | No — same, plus `agents/<name>/` |
| `ezra serve` / `ezra chat` | No |
| Grid **Cline** lane (file/shell tools) | **Yes** — some CLI, not necessarily the npm global |
| Grid **OpenClaw** lane | No Cline; needs an OpenClaw CLI — [OpenClaw](openclaw.md) |

Stay on **Local** if you only want to talk to the model. Use **Cline** when you
want the coding agent.

### How to get a Cline CLI (pick one)

EZRA looks in this order (`ezra cline status` shows what it found):

1. `EZRA_CLINE_CLI` or `cline.cli` in `ezra.yaml` (absolute path you set)
2. `cline` on `PATH`
3. Built `third_party/Cline/apps/cli/dist/index.js` (runs with Node)
4. Source `third_party/Cline/apps/cli/src/index.ts` (runs with **Bun 1.3+**)

| Option | When to use it |
|--------|----------------|
| **Skip Cline** | Chat only: Grid **Local** / **Agent**. Do not run `npm i -g cline`. |
| **`npm i -g cline`** (Node 22+) | Simplest on Windows. Puts `cline` on PATH. |
| **Bun 1.3+** | Keep using the vendored TypeScript at `third_party/Cline/…/index.ts`. Install from [bun.sh](https://bun.sh). |
| **Build the vendored tree** | Produce `dist/index.js` so Node can run it — [Cline README](../third_party/Cline/README.md). |
| **Point at a binary you already have** | `set EZRA_CLINE_CLI=C:\path\to\cline` (or `cline.cli` in `ezra.yaml`). |

Do **not** install Cline from the VS Marketplace for this flow. Grid is a
sideload; marketplace Cline is a different extension.

---

## 1. Pick a free model

Laptop / first try (already tagged `code` in the gallery):

```bash
ezra models download phi-3.5-mini-instruct
```

Stronger coding / longer edits (needs more RAM, ~6 GB):

```bash
ezra models download qwen2.5-7b-instruct
```

Smaller if RAM is tight:

```bash
ezra models download qwen2.5-3b-instruct
```

Check it landed:

```bash
ezra models status
ezra models info phi-3.5-mini-instruct
```

`ezra models recommend` ranks gallery models that fit this machine. Prefer
`--format gguf` for local Cline.

| Alias | Size | License | Gated | Notes |
|-------|------|---------|-------|--------|
| `phi-3.5-mini-instruct` | 3.8B | MIT | no | Good first coding GGUF |
| `qwen2.5-3b-instruct` | 3B | Apache-2.0 | no | Fast laptop default |
| `qwen2.5-7b-instruct` | 7B | Apache-2.0 | no | Better quality if it fits |
| `llama3.2-3b-instruct` | 3B | Llama-3.2 | no | Compact instruct |

Swap the alias in every command below if you pick a different name.

---

## 2. Serve it (keep this terminal open)

```bash
pip install -r requirements-ide-cpu.txt   # once; or cuda124 / macos — see getting-started.md

ezra serve --model phi-3.5-mini-instruct --host 127.0.0.1 --port 8000
```

Leave this running. Clients use:

```text
http://127.0.0.1:8000/v1
```

That is an OpenAI-compatible `/v1/chat/completions` server. Cline, the Grid,
Open WebUI, and the OpenAI Python SDK can all talk to it. Details:
[Conversation runtime](conversation.md).

Smoke test (optional):

```bash
ezra chat --model phi-3.5-mini-instruct -p "Say hello in one sentence."
```

---

## 3. Point Cline at EZRA (once)

Cline’s default providers want a paid cloud key. Skip them:

```bash
ezra cline status                 # CLI should resolve
npm i -g cline                    # only if status says CLI missing (Node 22+)
# other options: Bun, vendored build, or EZRA_CLINE_CLI — see above

ezra cline use-local --model phi-3.5-mini-instruct
ezra cline use-local --model phi-3.5-mini-instruct --auth
```

`--auth` writes Cline’s **openai-compatible** provider:

- base URL: `http://127.0.0.1:8000/v1`
- model: `phi-3.5-mini-instruct`
- key: `ezra-local` (placeholder only; EZRA serve does not check it)

It does **not** start a Cline agent session.

From a shell, without the Grid:

```bash
cline -P openai-compatible -k ezra-local -m phi-3.5-mini-instruct "List the Python packages in this repo"
```

Cline still asks before editing files or running commands.

---

## 4. Connect VS Code / Cursor (sideload Grid)

Do **not** install Cline from the VS Marketplace for this flow. Sideload EZRA
Grid from this checkout:

```bash
ezra ide install                  # every editor found (Cursor and/or VS Code)
ezra ide install --ide cursor     # Cursor only
ezra ide install --ide code       # VS Code only
```

Then in **Visual Studio Code** (for `--ide code`) or **Cursor** (for `--ide cursor`):

1. **Ctrl+Shift+P** → **Developer: Reload Window**
2. Open the Grid. EZRA is **not** under VS Code Chat / Copilot. Use any of:
   - **Ctrl+Shift+P** → **EZRA: Open Grid**
   - Far-left activity bar: **rising-columns** icon (often near the bottom; tooltip **EZRA Grid**)
   - Status bar: click **EZRA**
   - **View → Open View…** → `Grid`
3. If the panel cannot find `ezra`, set **EZRA Grid → `ezra.pythonPath`** to
   your venv Python (Windows example: `C:\Users\you\EZRA\.venv\Scripts\python.exe`)

Plain chat (no Cline): **Local** lane → pick the GGUF → type in the bottom box → **Ctrl+Enter**.

Cline coding agent: keep `ezra serve` running, then follow section 5.

Install details and settings: [EZRA Grid](ide.md).

---

## 5. Use Cline from the Grid

1. Keep `ezra serve …` running (step 2).
2. Open EZRA Grid.
3. Select the **Cline** lane (not Local — Local is `ezra chat` only).
4. Choose `phi-3.5-mini-instruct` (or whichever GGUF you served).
5. Type a coding task, **Ctrl+Enter** (macOS: **Cmd+Enter**).
6. A terminal opens with a `cline -P openai-compatible …` line. Confirm it.

Example prompts that stay on the local model:

- “Explain `src/ezra/cli.py`’s `doctor` command.”
- “Add a unit test for `serve_base_url` in `tests/test_cline.py`.”
- “Summarize TODO.md P0 items.”

The **Local** lane chats with the same GGUF but does **not** run Cline’s
file/shell tools. Use **Cline** when you want the coding agent.

---

## End-to-end checklist

```bash
# venv on, from the EZRA repo root
pip install -r requirements-ide-cpu.txt
ezra models download phi-3.5-mini-instruct
ezra serve --model phi-3.5-mini-instruct --host 127.0.0.1 --port 8000
# new terminal:
ezra cline use-local --model phi-3.5-mini-instruct --auth
ezra ide install --ide cursor    # or --ide code
```

Reload the editor → Grid → **Cline** lane → send.

---

## If something fails

| Symptom | What to do |
|---------|------------|
| `ezra serve` missing FastAPI | `pip install -r requirements-serve.txt` |
| Chat is empty / weights error | `pip install -r requirements-ide-cpu.txt` and `ezra models status` |
| `ezra cline status` has no CLI | `npm i -g cline` (Node 22+), or another [CLI option](#how-to-get-a-cline-cli-pick-one) |
| `Found … index.ts but bun is not on PATH` | Vendored source needs Bun, or install `npm i -g cline` so PATH wins |
| Port 8000 already in use | Another `ezra serve` (sometimes `--backend stub`) is bound. Stop that process, then start the real serve |
| Cline asks for Anthropic / OpenRouter | Re-run `ezra cline use-local --auth`; use `-P openai-compatible` |
| Grid cannot find `ezra` | Set `ezra.pythonPath` or `ezra.cliPath` |
| No chat / Copilot panel | EZRA is not VS Code Chat. **Ctrl+Shift+P** → **EZRA: Open Grid** |
| Grid Cline terminal errors on connect | Serve must be up on `127.0.0.1:8000` |
| Model not in the Grid dropdown | Download it, then **Refresh** in the Grid |
| Want a different free GGUF | Change `--model` on serve, `use-local`, and the Grid picker |

EZRA never auto-starts Cline, never starts OpenClaw’s Gateway, and never
publishes the Grid extension.
