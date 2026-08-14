# Getting started (no coding experience needed)

This page takes you from a fresh computer to **chatting with a free local
model inside VS Code or Cursor**. No cloud account. No marketplace install.

You will:

1. Install a few free programs
2. Copy EZRA onto your computer
3. Install the right **wheel** (pre-built library) for your machine
4. Download a small open model
5. Put **EZRA Grid** into VS Code
6. Send a message

If a command fails, copy the red text and the step number — that is enough for
someone to help you.

Related: [Install (short)](install.md) · [Which wheel](#3-install-ezra-and-the-right-wheel) ·
[EZRA Grid](ide.md) · [Cline + free model](cline-local.md)

---

## 0. Programs to install first

Install these like any other app. Restart the terminal (or VS Code) after.

| Program | Why | Where |
|---------|-----|--------|
| **Python 3.10 or newer** | Runs EZRA | [python.org/downloads](https://www.python.org/downloads/) — on Windows, tick **Add python.exe to PATH** |
| **Git** | Copies the EZRA folder | [git-scm.com](https://git-scm.com/downloads) |
| **Visual Studio Code** (or Cursor) | Where you chat | [code.visualstudio.com](https://code.visualstudio.com/) |

You do **not** need a C++ compiler if you use the wheel files below.

**Already have Anaconda / Miniconda?** You can skip making a `.venv`. Use that
Python’s `pip` in the steps below, then in VS Code set `ezra.pythonPath` to
that interpreter (for example
`C:\Users\YOURNAME\AppData\Local\anaconda3\python.exe`).

Open a terminal:

- Windows: **Command Prompt** or **PowerShell** (Start menu → type `powershell`)
- macOS: **Terminal**
- Linux: your usual terminal

---

## 1. Copy EZRA

```bash
git clone https://github.com/Awwal41/EZRA.git
cd EZRA
```

Stay in this `EZRA` folder for every later command.

---

## 2. Make a private Python folder (venv)

This keeps EZRA’s libraries off the rest of your computer.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If Windows blocks the script, run this once, then try Activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**Windows (Command Prompt):**

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

When it worked, the prompt starts with `(.venv)`.

Upgrade pip once:

```bash
python -m pip install -U pip
```

---

## 3. Install EZRA and the right wheel

A **wheel** is a ready-made `llama-cpp-python` build so your computer does not
compile C++ (that path is slow and often breaks on Windows).

### Pick one file

| Your computer | File to install |
|---------------|-----------------|
| Windows or Linux **without** an NVIDIA graphics card | `requirements-ide-cpu.txt` |
| NVIDIA GPU, `nvidia-smi` shows **CUDA 12.4** or 12.5 / 12.6 | `requirements-ide-cuda124.txt` |
| NVIDIA GPU, `nvidia-smi` shows **CUDA 12.1** | `requirements-ide-cuda121.txt` |
| Apple Mac with M1 / M2 / M3 / M4 | `requirements-ide-macos.txt` |

Not sure? Use **`requirements-ide-cpu.txt`**. It works on almost every laptop
(including Anaconda on Windows). CUDA wheel files work best with **Python
3.10, 3.11, or 3.12**.

To see CUDA (NVIDIA only), in the same terminal:

```bash
nvidia-smi
```

Look at **CUDA Version** in the top-right of that table. If the command is not
found, you do not have an NVIDIA driver — use the CPU file.

### Run it

**Windows example (CPU — most people):**

```powershell
pip install -r requirements-ide-cpu.txt
```

**NVIDIA CUDA 12.4:**

```powershell
pip install -r requirements-ide-cuda124.txt
```

**Mac:**

```bash
pip install -r requirements-ide-macos.txt
```

This also runs `pip install -e .`, which adds the `ezra` command.

**Good sign:** pip finishes in a few minutes and prints a `.whl` filename for
`llama-cpp-python`. It should **not** sit on `Building wheel for llama-cpp-python`.

**Bad sign:** that “Building wheel” line for a long time. Press **Ctrl+C**, then:

```powershell
pip install -r requirements-ide-cpu.txt --upgrade --force-reinstall
```

Check:

```bash
ezra doctor
```

You want `llama-cpp-python: ok` and `fastapi/uvicorn: ok`.

A one-page cheat sheet lives in [`requirements/README.md`](../requirements/README.md).

---

## 4. Download a free model

This is the open GGUF file EZRA runs on your disk. No API key.

Laptop / first try:

```bash
ezra models download phi-3.5-mini-instruct
```

Need a suggestion for this machine:

```bash
ezra models recommend
```

Wait until it says `downloaded` or `already_present`. Confirm:

```bash
ezra models status
```

You should see `phi-3.5-mini-instruct` with a size of about **2 GB**, not a few
bytes. (A few bytes means the download did not finish — run the download
command again with `--force`.)

---

## 5. Put EZRA Grid into VS Code (or Cursor)

Still in the `EZRA` folder, venv on:

```bash
ezra ide install --ide code
```

Cursor instead of VS Code:

```bash
ezra ide install --ide cursor
```

Both:

```bash
ezra ide install
```

This copies a private extension onto **this computer**. It is **not** uploaded
to the internet or the VS Marketplace.

---

## 6. Chat in VS Code

1. Open **Visual Studio Code** (the blue/grey Microsoft app).
2. **File → Open Folder…** and choose your `EZRA` folder (or any project).
3. Press **Ctrl+Shift+P** (Mac: **Cmd+Shift+P**).
4. Type `Reload Window` and run **Developer: Reload Window**.
5. Press **Ctrl+Shift+P** again, type `EZRA: Open Grid`, press Enter.

You can also click the **four rising columns** on the far-left bar (hover until
it says **EZRA Grid**).

If the panel says it cannot find `ezra`:

1. **File → Preferences → Settings** (Ctrl+,)
2. Search `ezra.pythonPath`
3. Paste the Python inside your venv:

   - Windows: `C:\Users\YOURNAME\EZRA\.venv\Scripts\python.exe`
   - macOS/Linux: `/Users/YOURNAME/EZRA/.venv/bin/python`

In the Grid:

1. Click **Local**.
2. Choose **phi-3.5-mini-instruct** (click **Refresh** if the list is empty).
3. Type `hello` in the bottom box.
4. Press **Ctrl+Enter** (Mac: **Cmd+Enter**) or **Send**.

The first real reply can take a minute while the model loads into RAM.

This is **not** Copilot / VS Code Chat. Use **EZRA: Open Grid** only.

---

## 7. Optional: Cline (coding agent) on the same model

Keep the model local — still no cloud key. Install **Node.js 22+** from
[nodejs.org](https://nodejs.org/) first if `npm` is not already on your PATH.

**Terminal A** (leave it open):

```bash
ezra serve --model phi-3.5-mini-instruct --host 127.0.0.1 --port 8000
```

**Terminal B** (venv on, same `EZRA` folder):

```bash
npm i -g cline
ezra cline use-local --model phi-3.5-mini-instruct --auth
```

In the Grid, pick the **Cline** lane, same model, send. A terminal opens; press
Enter to confirm. Full recipe: [Cline + a free EZRA model](cline-local.md).

---

## If something goes wrong

| What you see | What to do |
|--------------|------------|
| `python` is not recognized | Reinstall Python and tick **Add to PATH**, then open a **new** terminal |
| `Activate.ps1` cannot be loaded | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `ezra` is not recognized | Activate `.venv` again, then `pip install -e .` |
| `Building wheel for llama-cpp-python` for a long time | Ctrl+C, then `pip install -r requirements-ide-cpu.txt` |
| `llama-cpp-python: missing` in `ezra doctor` | Same CPU wheel file as above |
| Model size is a few bytes | `ezra models download phi-3.5-mini-instruct --force` |
| Grid: `ezra CLI not found` | Set `ezra.pythonPath` to `.venv\Scripts\python.exe` |
| Grid not in the sidebar | Command Palette → **EZRA: Open Grid**; reload the window |
| Reply never comes | First load is slow; or `ezra.backend` is `stub` (echo only) — set it to `auto` after the wheel install |
| NVIDIA file installed but no GPU | Uninstall is not required; install `requirements-ide-cpu.txt` on top |

---

## What you installed (plain language)

| Piece | Role |
|-------|------|
| `requirements.txt` | Basic EZRA libraries (download, config, CLI) |
| `requirements-ide-*.txt` | EZRA **plus** the chat server **plus** the llama.cpp **wheel** for your machine |
| Gallery GGUF | The actual open model weights on disk |
| EZRA Grid | Sidebar in VS Code / Cursor (sideload, not the store) |

You never need to “upload” these files. Everything stays on your computer.
