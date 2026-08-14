# EZRA - Shared TODO

Collaborative task list for contributors. **Anyone can add items** - keep entries short, assign a priority, and leave your handle/date if useful.

## How to add an item

1. Pick a section (or add a new one under **Backlog / Ideas**).
2. Copy a checkbox line and fill it in:

   ```markdown
   - [ ] **Short title** - one-line why / notes. `(@you, YYYY-MM-DD)` `P0|P1|P2`
   ```

3. Open a PR, or edit this file on `main` if you have write access.
4. When done: flip `[ ]` → `[x]` and (optional) link the PR: `(#123)`.

**Priority legend**

| Tag | Meaning |
|-----|---------|
| `P0` | MVP / blocks core value |
| `P1` | Important next |
| `P2` | Nice to have / later |
| `Idea` | Not committed - discuss first |

---

## Done / in progress

Track what already landed so we do not re-open finished work.

- [x] Package skeleton (`pyproject.toml`, `src/ezra`, GPL license)
- [x] Default config loader (`config.py` + `defaults/ezra.yaml` + `ezra.yaml.example` / `ezra init-config`)
- [x] Curated free-model gallery (`gallery/__init__.py` + `gallery/models.yaml`)
- [x] Hugging Face downloader (`downloader.py`)
- [x] CLI entrypoint (`cli.py`: `ezra models list|download`, `ezra doctor`, `ezra hpc`)
- [x] SBATCH generator + templates (`hpc/sbatch.py`, `scripts/hpc_*.sh`)
- [x] Gallery + SBATCH unit tests (`tests/test_gallery.py`, `tests/test_sbatch.py`)
- [x] Personal agent scaffolds (`agents/_template`, `ezra agents init|list|show|check`)
- [x] Conversation + local inference (`ezra.conversation`, `ezra.inference`, `ezra chat`, `ezra serve`)
- [x] Document parse module (`ezra.parse` + vendored MegaParse under `third_party/MegaParse`, `ezra parse`, `ezra chat --file`)
- [x] OpenClaw as full in-tree snapshot (`third_party/OpenClaw` @ v2026.6.34) + `ezra.openclaw` facade
- [x] Peekaboo / gogcli / MegaParse as full in-tree snapshots (no remaining third_party submodules)
- [x] Cline as full in-tree snapshot (`third_party/Cline` @ `afab68f3…`) + `ezra.cline` facade
- [x] EZRA Grid VS Code / Cursor extension (`ide/vscode`) + `ezra ide` sideload (no marketplace)

---

## P0 - MVP (must ship)

### Install & DX

- [ ] One-command install for CLI (`pip install -e .` docs + verified entrypoint) `P0`
- [ ] `ezra --help` / `ezra version` working end-to-end `P0`
- [ ] README quickstart: install → list models → download one model `P0`

### Model gallery & download

- [ ] `ezra models list` - show curated gallery (filters: size, tags, science) `P0`
- [ ] `ezra models download <name>` - download one model by alias `P0`
- [ ] `ezra models download --all` - download all gallery models (parallel + resume) `P0`
- [ ] Quant selection / auto-pick (GGUF Q4_K_M default; respect `prefer_quant`) `P0`
- [ ] Clear progress + resume on interrupted HPC downloads `P0`

### Document parsing

- [x] `ezra.parse` facade over MegaParse + basic backend `P0`
- [x] Vendor MegaParse Python sources (`third_party/MegaParse`, Apache-2.0) `P0`
- [x] CLI `ezra parse` + chat `--file` document context `P0`

### Local inference

- [x] llama.cpp backend (minimum viable load + chat/completion) `P0`
- [x] MLX backend (Apple Silicon) `P0`
- [x] OpenAI-compatible local HTTP API (`/v1/chat/completions`) `P0`
- [x] Simple multi-model switching (manual + basic auto) `P0`
- [x] Conversation session types (`ezra.conversation`: bind agent/model, messages, stub backend for tests) - design: `docs/conversation.md` `P0`

### Router (basic)

- [ ] Basic router: complexity heuristic + prefer-local / prefer-HPC policy `P0`
- [ ] Clear “which model answered” indicator in CLI/API metadata `P0`

### HPC / SLURM

- [x] Generate / run as **SBATCH script** so jobs get GPUs, CPUs, memory, time limits `P0`
- [x] Example `#SBATCH` templates (GPU serve, CPU download, interactive) - `scripts/hpc_*.sh` + `ezra hpc` `P0`
- [x] Document cluster env vars (`EZRA_HOME`, `EZRA_MODELS_DIR`, `HF_TOKEN`, modules/CUDA) `P0`
- [x] `ezra hpc submit` that wraps download/serve/interactive in sbatch `P0`

---

## P1 - Important next

- [ ] HPC OpenAI-compatible remote endpoints in config + client `P1`
- [ ] Chemistry / materials system prompt pack `P1`
- [x] Wire `agents/<name>/` prompts + preferred models into local chat / serve `P1`
- [x] `ezra chat` CLI (agent or model) on top of conversation runtime `P1`
- [x] `ezra serve --agent` / `model=agent:<name>` in `/v1/chat/completions` `P1`
- [x] Session saving + basic experiment notes (`~/.ezra/sessions/`) `P1`
- [x] Docs recipe: point Gradio / Open WebUI at local `ezra serve` `P1`
- [ ] Resource monitor (RAM / VRAM) to prevent OOM crashes `P1`
- [ ] Streaming responses through local API and HPC bridge `P1`
- [ ] Health checks + simple fallback chain when a model/endpoint is down `P1`

---

## P2 - Later / Phase 3-4

- [ ] Domain classifier (SMILES/CIF, chem terminology, long-context signals) `P2`
- [ ] Full policy engine (privacy-first, long-context → HPC, tag matching) `P2`
- [ ] vLLM / other GPU backends `P2`
- [x] Desktop or web UI (gallery + chat + router settings) `P2` — **partial:** sideload IDE Grid (`docs/ide.md`); full lab UI still later
- [ ] Scientific tool-calling hooks (PubChem, RDKit-style, ASE/pymatgen) `P2`
- [ ] Domain RAG helpers + lightweight chem/materials eval harness `P2`
- [ ] Ship / fetch MegaParse DocLayNet ONNX for hi_res layout (currently excluded from git) `P2`
- [ ] Plugin system for custom routers / backends / tools `P2`
- [ ] Lab-shared exportable configs + multi-user notes `P2`
- [ ] Multimodal inputs (structures, spectra, lab images) `Idea`

---

## Backlog / Ideas

_Drop anything here - no commitment required. Promote to P0/P1/P2 when agreed._

- [ ] Visual multi-agent / workflow canvas (conversation runtime stays HTTP + Python API first) `Idea`
- [ ] `ezra hpc submit serve --agent <name>` once serve binds agent profiles `Idea`
- [x] Vendor Peekaboo as `third_party/Peekaboo` submodule + `ezra.peekaboo` adapter / MCP helpers `P2`
- [x] Vendor gogcli as `third_party/gogcli` submodule + `ezra.gog` adapter / MCP helpers `P2`
- [ ] Wire Peekaboo captures into agent chat multimodal turns (macOS) `Idea`
- [ ] Wire `ezra gog run` into agent tool-calling (readonly defaults) `Idea`
- [ ] Promote MegaParse checkout to a proper git submodule (match Peekaboo layout) `Idea`

---

## Notes for collaborators

- Prefer small PRs that flip one or a few checkboxes.
- Match existing style under `src/ezra/` (type hints, dataclasses, YAML config).
- Do not commit secrets (HF tokens, cluster credentials). Use env vars only.
- When adding gallery models, keep them **free/open** and document gated licenses in `models.yaml`.
