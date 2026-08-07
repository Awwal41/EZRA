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

### Local inference

- [ ] llama.cpp backend (minimum viable load + chat/completion) `P0`
- [ ] MLX backend (Apple Silicon) `P0`
- [ ] OpenAI-compatible local HTTP API (`/v1/chat/completions`) `P0`
- [ ] Simple multi-model switching (manual + basic auto) `P0`

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
- [ ] Wire `agents/<name>/` prompts + preferred models into local chat / serve `P1`
- [ ] Session saving + basic experiment notes `P1`
- [ ] Resource monitor (RAM / VRAM) to prevent OOM crashes `P1`
- [ ] Streaming responses through local API and HPC bridge `P1`
- [ ] Health checks + simple fallback chain when a model/endpoint is down `P1`

---

## P2 - Later / Phase 3-4

- [ ] Domain classifier (SMILES/CIF, chem terminology, long-context signals) `P2`
- [ ] Full policy engine (privacy-first, long-context → HPC, tag matching) `P2`
- [ ] vLLM / other GPU backends `P2`
- [ ] Desktop or web UI (gallery + chat + router settings) `P2`
- [ ] Scientific tool-calling hooks (PubChem, RDKit-style, ASE/pymatgen) `P2`
- [ ] Domain RAG helpers + lightweight chem/materials eval harness `P2`
- [ ] Plugin system for custom routers / backends / tools `P2`
- [ ] Lab-shared exportable configs + multi-user notes `P2`
- [ ] Multimodal inputs (structures, spectra, lab images) `Idea`

---

## Backlog / Ideas

_Drop anything here - no commitment required. Promote to P0/P1/P2 when agreed._

- [ ] …
- [ ] …

---

## Notes for collaborators

- Prefer small PRs that flip one or a few checkboxes.
- Match existing style under `src/ezra/` (type hints, dataclasses, YAML config).
- Do not commit secrets (HF tokens, cluster credentials). Use env vars only.
- When adding gallery models, keep them **free/open** and document gated licenses in `models.yaml`.
