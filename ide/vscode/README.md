# EZRA Grid (sideload only)

Off-grid switchboard for **VS Code** and **Cursor**. Four lanes, one panel:

| Lane | What it does |
|------|----------------|
| **EZRA local** | `ezra chat` against a gallery GGUF on this machine |
| **Agent** | Binds `agents/<name>/` (prompt + preferred models) |
| **Cline** | Hands your prompt to Cline using **EZRA downloaded models** via `ezra serve` (no cloud API key) |
| **OpenClaw** | Hands your prompt to the vendored OpenClaw CLI in a terminal (you opt in) |

This package is **`private`: true**. Do **not** publish it to the VS Marketplace or Open VSX. Install from your EZRA checkout:

```bash
ezra ide package
ezra ide install --ide code      # Visual Studio Code
ezra ide install --ide cursor    # Cursor
```

## Chat in VS Code (not Copilot)

EZRA does **not** appear in VS Code **Chat** or the marketplace. After install:

1. **Ctrl+Shift+P** → **Developer: Reload Window**
2. **Ctrl+Shift+P** → **EZRA: Open Grid**
3. Or click the **rising-columns** icon on the far-left activity bar (often near the bottom), or the **EZRA** item on the status bar
4. Click **Local**, pick a model, type in the bottom box, **Ctrl+Enter** (macOS: **Cmd+Enter**)

If the activity-bar icon is missing: right-click the activity bar → enable **EZRA Grid**, or **View → Open View… → Grid**.

If the panel says `ezra CLI not found`, set **EZRA Grid → `ezra.pythonPath`** to your venv Python (Windows: `C:\Users\you\EZRA\.venv\Scripts\python.exe`).

Full walkthrough: [docs/ide.md](../../docs/ide.md).

**Cline without a paid key:** keep `ezra serve --model <gguf>` running, then
`ezra cline use-local --auth`. Walkthrough: [docs/cline-local.md](../../docs/cline-local.md).

Safety: EZRA never auto-installs the extension, never auto-starts Cline, and never starts the OpenClaw Gateway. Cline / OpenClaw only run when you select that lane and send.

License: GPL-3.0-or-later (same as EZRA).
