# Contributing to EZRA

Thanks for helping build **EZRA** - a researcher-first toolkit for downloading, running, and routing free/open LLMs for materials science and chemistry.

This guide covers forking the repo, setting up a dev environment, coding style, common contribution types, and opening pull requests.

## Code of conduct

Be respectful, assume good intent, and keep discussion focused on the work. Harassment or discriminatory language is not welcome.

## License

EZRA is **GPL-3.0-or-later**. By contributing, you agree that your contributions are licensed under the same terms. See [LICENSE](LICENSE).

---

## 1. Fork and clone

Day-to-day work happens on **`develop`**. Stable releases land on **`main`** via pull request (`develop` → `main`). Do not commit feature work straight to `main`.

1. On GitHub, open [Awwal41/EZRA](https://github.com/Awwal41/EZRA) and click **Fork**.
2. Clone **your** fork (replace `YOUR_USER` with your GitHub username):

   ```bash
   git clone https://github.com/YOUR_USER/EZRA.git
   cd EZRA
   ```

3. Add the upstream remote so you can stay in sync:

   ```bash
   git remote add upstream https://github.com/Awwal41/EZRA.git
   git fetch upstream
   git remote -v
   ```

4. Check out **`develop`**, then create a branch for your work:

   ```bash
   git checkout develop
   git pull upstream develop   # or: origin develop if you push there directly
   git checkout -b feature/short-description
   # or: fix/…, docs/…, gallery/…
   ```

### Keep your fork up to date

```bash
git fetch upstream
git checkout develop
git merge upstream/develop   # or: git rebase upstream/develop
git push origin develop
```

Rebase or merge `develop` into your feature branch before opening or updating a PR.

---

## 2. Development setup

Python **3.10+** is required.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS / HPC
source .venv/bin/activate

pip install -e ".[dev]"
# optional: documentation site (Sphinx + MyST)
pip install -e ".[docs]"
ezra doctor
```

Run tests:

```bash
pytest
```

Build HTML docs:

```bash
cd docs
make html          # Linux / macOS
# Windows: .\make.bat html
# open _build/html/index.html
```

Lint / format with Ruff (listed under `[project.optional-dependencies] dev`):

```bash
ruff check src tests
ruff format src tests
```

Do **not** commit model weights (`.gguf`, `.safetensors`), `.venv/`, `.env`, repo-root `ezra.yaml`, or secrets. Copy from `ezra.yaml.example` / `.env.example` (or `ezra init-config`). See [.gitignore](.gitignore).

---

## 3. Project layout

| Path | Purpose |
|------|---------|
| `src/ezra/` | Package source (`src` layout) |
| `src/ezra/gallery/models.yaml` | Curated free/open model gallery |
| `src/ezra/defaults/ezra.yaml` | Packaged default config |
| `ezra.yaml.example` / `.env.example` | User-copy templates (local files are gitignored) |
| `src/ezra/cli.py` | Click CLI (`ezra` entrypoint) |
| `src/ezra/hpc/` | SLURM / SBATCH helpers |
| `scripts/hpc_*.sh` | Example HPC job scripts (honor `EZRA_SITE`) |
| `sites/` | Per-cluster profiles (`init-site` → edit → commit & push) |
| `agents/` | Personal agent scaffolds (`agents init` → edit prompt/models) |
| `docs/` | User guides (Markdown) + Sphinx site (`conf.py`, `index.rst`, MyST) |
| `tests/` | Pytest suite (prefer no network) |
| `TODO.md` | Shared backlog - anyone can add items |

Match existing module boundaries: gallery data in YAML, download logic in `downloader.py`, config in `config.py`, agents in `agents.py`, CLI thin wrappers in `cli.py`.

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
- Avoid broad `except:`; catch specific exceptions and fail with clear messages.
- Do not add heavy dependencies without discussion - keep the core install lean for HPC/login nodes.

### Formatting and lint

- Format and lint with **Ruff** before opening a PR.
- Prefer readable line lengths; follow what Ruff/`ruff format` produces.
- Imports: stdlib → third party → local (`ezra.…`), matching existing files.

### YAML (gallery & config)

- Only list models that are **downloadable without payment**. Mark `gated: true` when a free HF account / license accept is still required.
- Use stable, lowercase **kebab-case** `name` aliases (`qwen2.5-7b-instruct`).
- Fill the documented fields (see the header comment in `models.yaml`): `repo_id`, `format`, `license`, tags, `description`, size guidance, and `file_pattern` / `files` when needed for GGUF.
- Keep names **unique** across the gallery.
- Prefer appending new models in the appropriate section (laptop / science / HPC) rather than rewriting unrelated entries.

### Shell (HPC scripts)

- Use `#!/usr/bin/env bash` and `set -euo pipefail`.
- Prefer environment variables already documented in the README (`EZRA_MODELS_DIR`, `EZRA_ROOT`, `MODEL`, …).
- Keep scripts HPC-friendly: no GUI assumptions; comment where sites should `module load …`.

### Docs and TODO

- Keep [README.md](README.md) examples and guides under [docs/](docs/README.md) accurate when you change CLI flags or behavior.
- User-facing how-to (install, models, agents, HPC, config, CLI) lives in `docs/` - update the matching page, not only the README.
- Shared ideas go in [TODO.md](TODO.md) with priority tags (`P0` / `P1` / `P2` / `Idea`).

---

## 5. Common contribution types

### Add a model to the gallery

1. Edit `src/ezra/gallery/models.yaml` - append an entry with the fields documented at the top of that file.
2. Confirm the HF `repo_id` exists and the license is acceptable for free/open use.
3. Run:

   ```bash
   ezra models list --query YOUR-NAME
   ezra models info YOUR-NAME
   pytest tests/test_gallery.py
   ```

4. No Python change is required for a pure gallery addition.

### Fix a bug or add a CLI feature

1. Branch from up-to-date `develop`.
2. Implement the smallest change that solves the problem.
3. Add or update tests under `tests/` (unit tests should not require network or GPUs).
4. Run `pytest` and `ruff check` / `ruff format`.
5. Update README / help text if user-facing behavior changes.

### HPC / SBATCH / site profiles

**Cluster-specific settings belong in `sites/<name>/`, not as one-off edits everyone has to rediscover.**

1. `ezra hpc init-site <cluster-name>`
2. Edit `EDIT ME` fields in `ezra.yaml` + `modules.sh`; fill `NOTES.md`
3. `export EZRA_SITE=<cluster-name>` and smoke-test with `--dry-run`
4. Commit `sites/<cluster-name>/` (no tokens) and open a PR

Details: [`sites/README.md`](sites/README.md) and [docs/hpc.md](docs/hpc.md).

- Prefer extending `src/ezra/hpc/sbatch.py` / `sites.py` and keeping `scripts/hpc_*.sh` as thin examples that honor `EZRA_SITE`.
- Cover new template logic in `tests/test_sbatch.py` / `tests/test_sites.py` where practical.

### Personal agents

**Domain prompts and preferred models belong in `agents/<name>/`, not hard-coded in the CLI.**

1. `ezra agents init <name>` (or start from `agents/chem-assistant/`)
2. Edit `agent.yaml` (gallery aliases) + `prompt.md`; fill `NOTES.md`
3. `ezra agents check <name>` and confirm aliases resolve
4. Commit shareable agents (no secrets); keep private work under `agents/local/`

Details: [`agents/README.md`](agents/README.md) and [docs/agents.md](docs/agents.md).

---

## 6. Tests

- Framework: **pytest**.
- Prefer **no network** in unit tests (dry-run downloads, tmp paths, fixtures).
- Name tests `test_*.py` / `test_*` functions.
- After gallery or filter changes, run at least `tests/test_gallery.py`.

```bash
pytest
pytest tests/test_gallery.py -q
```

---

## 7. Commits and pull requests

### Commits

- Small, focused commits with clear messages (what + why).
- Example: `Add ChemBERTa gallery entry for chemistry tagging`.
- Do not commit secrets, tokens, or large binary weights.

### Open a PR

**Default:** feature / fix / docs PRs target **`develop`**.

**Release:** maintainers open (or accept) a PR from **`develop` → `main`** when a batch is ready to ship.

1. Push your branch to **your fork** (or to `origin` if you have write access):

   ```bash
   git push -u origin feature/short-description
   ```

2. Open a pull request against `Awwal41/EZRA` → **`develop`** (not `main`, unless this is an intentional release PR).
3. In the PR description, include:
   - **What** changed and **why**
   - How you tested (`pytest`, `ezra doctor`, dry-run download, …)
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

---

## 8. Questions and roadmap

- User how-to: [docs/](docs/README.md)
- Near-term work and ideas: [TODO.md](TODO.md)
- Product vision / phases: [README.md](README.md) (Vision section)
- Bugs and feature proposals: GitHub Issues on the upstream repo

If you are unsure where a change belongs, open a short issue or draft PR first - especially for new dependencies, runtime backends, or Phase 2+ routing work.
