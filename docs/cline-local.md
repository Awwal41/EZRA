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

Related: [Cline facade](cline.md) · [EZRA Grid](ide.md) · [Models](models.md) ·
[Conversation / serve](conversation.md).

---

## What you need

| Piece | Why |
|-------|-----|
| EZRA checkout + venv | `ezra` CLI, gallery, serve |
| A **free GGUF** from the gallery | The actual model Cline will call |
| `pip install -e ".[local,serve]"` | llama.cpp + OpenAI HTTP |
| Cline CLI (`npm i -g cline`, Node 22+) | Coding agent (vendored sources are already in-tree) |
| VS Code or Cursor | Where Grid lives |

No cloud API key. `HF_TOKEN` is only if you pick a **gated** gallery entry
(Meta/Google license click-through). The models in this guide are **not gated**.

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
pip install -e ".[local,serve]"   # once per venv

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

Then in the editor:

1. **Developer: Reload Window**
2. Click the **rising-columns** icon in the activity bar (EZRA Grid)
3. If the panel cannot find `ezra`, set **EZRA Grid → `ezra.pythonPath`** to
   your venv Python (Windows example: `C:\Users\you\EZRA\.venv\Scripts\python.exe`)

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
pip install -e ".[local,serve]"
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
| `ezra serve` missing FastAPI | `pip install -e ".[serve]"` |
| Chat is empty / weights error | `pip install -e ".[local]"` and `ezra models status` |
| `ezra cline status` has no CLI | `npm i -g cline` (Node 22+) |
| Cline asks for Anthropic / OpenRouter | Re-run `ezra cline use-local --auth`; use `-P openai-compatible` |
| Grid cannot find `ezra` | Set `ezra.pythonPath` or `ezra.cliPath` |
| Grid Cline terminal errors on connect | Serve must be up on `127.0.0.1:8000` |
| Model not in the Grid dropdown | Download it, then **Refresh** in the Grid |
| Want a different free GGUF | Change `--model` on serve, `use-local`, and the Grid picker |

EZRA never auto-starts Cline, never starts OpenClaw’s Gateway, and never
publishes the Grid extension.
