# Contributing to EZRA

Thanks for helping build **EZRA** - a researcher-first toolkit for downloading, running, and routing free/open LLMs for materials science and chemistry.

This guide walks through forking the repo, setting up a dev environment, coding style, common contribution types, tests, and opening pull requests.

## Code of conduct

Be respectful, assume good intent, and keep discussion focused on the work. Harassment or discriminatory language is not welcome.

## License

EZRA is **GPL-3.0-or-later**. By contributing, you agree that your contributions are licensed under the same terms. See [LICENSE](LICENSE).

Vendored third-party code under `third_party/` keeps its upstream license (MegaParse is **Apache-2.0**). Do not relicense those trees; keep `LICENSE` / `NOTICE` / `UPSTREAM.txt` when refreshing.

---

## Branching model

| Branch | Role |
|--------|------|
| `develop` | Default integration branch. Day-to-day features, fixes, and docs land here. |
| `main` | Stable releases only. Updated via pull request from `develop` when a batch is ready to ship. |

**Rules of thumb:**

- Open feature / fix / docs PRs against **`develop`**, not `main`.
- Do not commit feature work straight to `main`.
- Maintainers (or release PRs) merge **`develop` → `main`** when shipping.
- Prefer short-lived topic branches: `feature/...`, `fix/...`, `docs/...`, `gallery/...`, `sites/...`.

Docs CI **builds** on `develop` and on PRs; the HTML site **deploys** from `main` (GitHub Pages).

---

## 1. Fork and clone

1. On GitHub, open [Awwal41/EZRA](https://github.com/Awwal41/EZRA) and click **Fork**.
2. Clone **your** fork (replace `YOUR_USER` with your GitHub username):

   ```bash
   git clone https://github.com/YOUR_USER/EZRA.git
   cd EZRA
   ```

   Third-party trees under `third_party/` (OpenClaw, Peekaboo, gogcli, MegaParse)
   are **full in-tree snapshots** (not submodules). See
   [`third_party/README.md`](third_party/README.md).

3. Add the upstream remote so you can stay in sync with the canonical repo:

   ```bash
   git remote add upstream https://github.com/Awwal41/EZRA.git
   git fetch upstream
   git remote -v
   ```

   You should see `origin` (your fork) and `upstream` (`Awwal41/EZRA`).

4. Check out **`develop`**, update it, then create a branch for your work:

   ```bash
   git checkout develop
   git pull upstream develop   # or: origin develop if you push there directly
   git checkout -b feature/short-description
   # examples: fix/download-retry, docs/install-windows, gallery/chemberta, sites/my-cluster
   ```

### Keep your fork up to date

Before starting new work (and again before opening or updating a PR):

```bash
git fetch upstream
git checkout develop
git merge upstream/develop   # or: git rebase upstream/develop
git push origin develop
```

Then bring your feature branch current:

```bash
git checkout feature/short-description
git merge develop            # or: git rebase develop
```

Resolve any conflicts locally, re-run tests, then push.

### After your PR is merged

```bash
git checkout develop
git pull upstream develop
git push origin develop
git branch -d feature/short-description   # optional: delete local topic branch
```

---

## 2. Development setup

**Requirements:** Python **3.10+**. No GPU is required for gallery work, downloads in dry-run mode, or most unit tests.

### Create a virtualenv and install

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS / HPC
source .venv/bin/activate

pip install -U pip
pip install -e ".[dev]"
# optional: Sphinx + MyST documentation site
pip install -e ".[docs]"
```

| Extra | What it adds |
|-------|----------------|
| (none) / bare `pip install -e .` | Runtime CLI and library |
| `[dev]` | Pytest, Ruff, and other contributor tools |
| `[docs]` | Sphinx, MyST, Furo theme for `docs/` HTML builds |

### Sanity-check the install

```bash
ezra doctor
ezra models list
```

`ezra doctor` reports the models directory, HF token status, gallery size, CPU/RAM/GPU fit budget, and whether the models path is writable. Fix anything it flags before relying on downloads.

### Run tests

```bash
pytest
pytest tests/test_gallery.py -q
```

### Build HTML docs

```bash
cd docs
make html          # Linux / macOS
# Windows: .\make.bat html
# open _build/html/index.html
```

### Lint and format

Ruff is listed under `[project.optional-dependencies] dev`:

```bash
ruff check src tests
ruff format src tests
```

Run both before opening a PR.

### Do not commit

- Model weights (`.gguf`, `.safetensors`, large snapshots)
- `.venv/`, `.env`, repo-root `ezra.yaml`
- HF tokens, passwords, or private cluster credentials

Copy templates from `ezra.yaml.example` / `.env.example`, or run `ezra init-config`. See [.gitignore](.gitignore).

---

## 3. Project layout

| Path | Purpose |
|------|---------|
| `src/ezra/` | Package source (`src` layout) |
| `src/ezra/gallery/models.yaml` | Curated free/open model gallery |
| `src/ezra/defaults/ezra.yaml` | Packaged default config |
| `ezra.yaml.example` / `.env.example` | User-copy templates (local files are gitignored) |
| `src/ezra/cli.py` | Click CLI (`ezra` entrypoint) |
| `src/ezra/downloader.py` | Hugging Face download / snapshot helpers |
| `src/ezra/config.py` | Config loading and env overlays |
| `src/ezra/agents.py` | Personal agent discovery and validation |
| `src/ezra/hpc/` | SLURM / SBATCH helpers and site loading |
| `scripts/hpc_*.sh` | Example HPC job scripts (honor `EZRA_SITE`) |
| `sites/` | Per-cluster profiles (`init-site` then edit, commit, push) |
| `agents/` | Personal agent scaffolds (`agents init` then edit prompt/models) |
| `docs/` | User guides (Markdown) + Sphinx site (`conf.py`, `index.rst`, MyST) |
| `tests/` | Pytest suite (prefer no network) |
| `TODO.md` | Shared backlog - anyone can add items |

**Module boundaries:** gallery data stays in YAML; download logic in `downloader.py`; config in `config.py`; agents in `agents.py`; document parsing in `ezra.parse` (wrap vendored MegaParse — do not import `megaparse` from other EZRA modules); CLI commands in `cli.py` should stay thin wrappers around library code.

---

## 4. Coding style

Follow patterns already used in the tree. Prefer consistency over personal preference.

### Python

- **Python 3.10+** syntax; use `from __future__ import annotations` at the top of modules.
- Prefer **type hints** on public functions and dataclasses (`Path | None`, `tuple[str, ...]`, etc.).
- Prefer **`pathlib.Path`** over raw string paths.
- Use **dataclasses** for structured data (see `ModelSpec`, `EzraConfig`).
- Keep functions focused; private helpers may use a leading `_`.
- CLI: **Click** groups/commands; user-facing tables/output via **Rich** where the rest of the CLI does.
- Avoid bare `except:`; catch specific exceptions and fail with clear messages.
- Do not add heavy dependencies without discussion - keep the core install lean for HPC and login nodes.

### Formatting and lint

- Format and lint with **Ruff** before opening a PR.
- Prefer readable line lengths; follow what `ruff format` produces.
- Imports: stdlib, then third party, then local (`ezra....`), matching existing files.

### YAML (gallery and config)

- Only list models that are **downloadable without payment**. Mark `gated: true` when a free HF account / license accept is still required.
- Use stable, lowercase **kebab-case** `name` aliases (`qwen2.5-7b-instruct`).
- Keep names **unique** across the gallery.
- Prefer appending new models in the appropriate section (laptop / science / HPC) rather than rewriting unrelated entries.

Documented gallery fields (see the header comment in `models.yaml`):

| Field | Notes |
|-------|--------|
| `name` | CLI alias for `ezra models download <name>` |
| `repo_id` | Hugging Face repo id |
| `format` | `gguf`, `safetensors`, or `mlx` |
| `license` | Short SPDX-ish label |
| `gated` | `true` if HF license gate required |
| `description` | One-line summary |
| `science_tags` / `tags` | Relevance and capability tags |
| `size_b` / `params` / `recommended_ram_gb` | Size guidance for recommend/fit |
| `file_pattern` / `files` / `quant` | Needed for many GGUF repos |
| `revision` | Optional git revision / branch |

### Shell (HPC scripts)

- Use `#!/usr/bin/env bash` and `set -euo pipefail`.
- Prefer environment variables already documented in the README (`EZRA_MODELS_DIR`, `EZRA_ROOT`, `MODEL`, and related).
- Keep scripts HPC-friendly: no GUI assumptions; comment where sites should `module load ...`.

### Docs and TODO

- Keep [README.md](README.md) examples and guides under [docs/](docs/README.md) accurate when you change CLI flags or behavior.
- User-facing how-to (install, models, agents, HPC, config, CLI) lives in `docs/` - update the matching page, not only the README.
- Shared ideas go in [TODO.md](TODO.md) with priority tags (`P0` / `P1` / `P2` / `Idea`).
- Avoid em dashes in docs; prefer commas, colons, parentheses, or a plain hyphen.

---

## 5. Common contribution types

### Add a model to the gallery

This is often the smallest useful PR and usually needs **no Python changes**.

1. Edit `src/ezra/gallery/models.yaml` - append an entry with the fields in the table above.
2. Confirm the Hugging Face `repo_id` exists and the license is acceptable for free/open use.
3. If the repo is GGUF, set `file_pattern` or `files` so downloads do not pull every quant.
4. Run:

   ```bash
   ezra models list --query YOUR-NAME
   ezra models info YOUR-NAME
   pytest tests/test_gallery.py
   ```

5. In the PR, note why the model fits materials/chemistry (or general local use) and roughly who it is for (laptop vs HPC).

### Fix a bug or add a CLI feature

1. Branch from up-to-date `develop`.
2. Implement the smallest change that solves the problem.
3. Add or update tests under `tests/` (unit tests should not require network or GPUs).
4. Run `pytest` and `ruff check` / `ruff format`.
5. Update README, the matching `docs/*.md` page, and CLI `--help` text if user-facing behavior changes.

### Documentation

1. Prefer editing the guide under `docs/` that users will read (for example `docs/install.md`, `docs/models.md`).
2. Keep the Sphinx toctree in `docs/index.rst` in sync if you add a new page.
3. Build locally with `pip install -e ".[docs]"` and `make html` (or `.\make.bat html` on Windows).
4. Contributor workflow detail belongs in this file (`CONTRIBUTING.md`); `docs/contributing.rst` should stay aligned with it.

### HPC / SBATCH / site profiles

**Cluster-specific settings belong in `sites/<name>/`, not as one-off edits everyone has to rediscover.**

1. `ezra hpc init-site <cluster-name>`
2. Edit `EDIT ME` fields in `ezra.yaml` and `modules.sh`; fill `NOTES.md` with partition, account, scratch, and module notes.
3. `export EZRA_SITE=<cluster-name>` and smoke-test with `--dry-run`:

   ```bash
   ezra doctor
   ezra hpc submit download --dry-run
   ```

4. Commit `sites/<cluster-name>/` (no tokens) and open a PR against `develop`.

Details: [`sites/README.md`](sites/README.md) and [docs/hpc.md](docs/hpc.md).

- Prefer extending `src/ezra/hpc/sbatch.py` / `sites.py` and keeping `scripts/hpc_*.sh` as thin examples that honor `EZRA_SITE`.
- Cover new template logic in `tests/test_sbatch.py` / `tests/test_sites.py` where practical.

### Personal agents

**Domain prompts and preferred models belong in `agents/<name>/`, not hard-coded in the CLI.**

Full step-by-step (recommend models, edit YAML/prompt, validate, download): [docs/agents.md](docs/agents.md).

Condensed workflow:

1. Install and sanity-check: `pip install -e .` then `ezra doctor`.
2. Choose shareable (`ezra agents init my-lab-assistant`) or private (`ezra agents init local/scratch-bot`).
3. Pick models that fit this machine: `ezra models recommend chemistry` (or another keyword).
4. Edit `agents/<name>/agent.yaml`: set `models.preferred`, `models.fallback`, `models.tags`, `science_focus`.
5. Edit `prompt.md`: role, priorities, typical tasks, style, boundaries (no invented citations / secrets).
6. Fill `NOTES.md` for humans (owner, hardware, intent).
7. Validate: `ezra agents check <name>` and `ezra agents show <name> --prompt`.
8. Download pinned aliases: `ezra models download <alias> ...`
9. Iterate on prompt and prefs; re-run `check` after YAML edits.
10. Commit shareable agents only (no tokens or private lab data). Keep experiments under `agents/local/`.

```bash
ezra agents init my-lab-assistant --description "Materials lab Q&A"
ezra models recommend chemistry
# edit agents/my-lab-assistant/agent.yaml and prompt.md
ezra agents check my-lab-assistant
ezra models download chemllm-7b qwen2.5-7b-instruct
ezra agents show chem-assistant --prompt   # study the shipped example
```

Details: [`agents/README.md`](agents/README.md) and [docs/agents.md](docs/agents.md).

Phase 1 is scaffold + gallery checks. When serve/routing land, the same `agent.yaml` + `prompt.md` will drive chat without re-scaffolding.

---

## 6. Tests

- Framework: **pytest**.
- Prefer **no network** in unit tests (dry-run downloads, tmp paths, fixtures).
- Name tests `test_*.py` / `test_*` functions.
- After gallery or filter changes, run at least `tests/test_gallery.py`.
- After agent or site changes, run the matching `tests/test_agents.py` / `tests/test_sites.py` (and `tests/test_sbatch.py` for submit templates).

```bash
pytest
pytest tests/test_gallery.py -q
pytest tests/test_agents.py tests/test_sites.py -q
```

---

## 7. Commits and pull requests

### Commits

- Small, focused commits with clear messages (what + why).
- Example: `Add ChemBERTa gallery entry for chemistry tagging`.
- Do not commit secrets, tokens, or large binary weights.
- Prefer one logical change per commit when practical; squash is optional during review.

### Open a PR

**Default:** feature / fix / docs / gallery / sites / agents PRs target **`develop`**.

**Release:** maintainers open (or accept) a PR from **`develop` → `main`** when a batch is ready to ship.

1. Push your branch to **your fork** (or to `origin` if you have write access):

   ```bash
   git push -u origin feature/short-description
   ```

2. Open a pull request against `Awwal41/EZRA` with base **`develop`** (not `main`, unless this is an intentional release PR).
3. In the PR description, include:
   - **What** changed and **why**
   - How you tested (`pytest`, `ezra doctor`, dry-run download, docs build, and similar)
   - Related TODO item or issue, if any
4. Expect review feedback; push additional commits to the same branch to update the PR.

### PR checklist

- [ ] Branch is up to date with `upstream/develop`
- [ ] Base branch is `develop` (or `main` only for a release merge)
- [ ] `pip install -e ".[dev]"` works
- [ ] `pytest` passes
- [ ] `ruff check` / `ruff format` clean (or intentional, noted exceptions)
- [ ] Gallery names unique; new models documented and free/open
- [ ] No secrets, weights, or `.venv` in the diff
- [ ] README / `docs/` / CLI help updated if behavior changed
- [ ] Docs build succeeds if you touched `docs/` (`make html` / `.\make.bat html`)

---

## 8. Questions and roadmap

- User how-to: [docs/](docs/README.md)
- Near-term work and ideas: [TODO.md](TODO.md)
- Product vision / phases: [README.md](README.md) (Vision section)
- Bugs and feature proposals: GitHub Issues on the upstream repo
- Live docs: [GitHub Pages](https://awwal41.github.io/EZRA/), [Read the Docs](https://ezra.readthedocs.io/), and optional [Vercel](docs/README.md#3-vercel-optional-shareable-url)

If you are unsure where a change belongs, open a short issue or draft PR first - especially for new dependencies, runtime backends, or Phase 2+ routing work.
