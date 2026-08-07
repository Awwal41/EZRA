# EZRA documentation

Guides live here as **Markdown** (easy to read on GitHub) and are built into an
HTML site with **Sphinx** + **MyST** + **reStructuredText**.

| Guide | When to read it |
|-------|-----------------|
| [Installation](install.md) | First-time setup (venv, `pip install`, `ezra doctor`) |
| [Models](models.md) | Recommend by hardware + keyword, browse, download, status, remove |
| [Personal agents](agents.md) | Scaffold your own assistant (prompt + preferred models) |
| [HPC / SLURM](hpc.md) | Site profiles, scratch paths, SBATCH submit |
| [Site profiles](sites.md) | Customize partition/modules for your cluster ([full notes](../sites/README.md)) |
| [Configuration](configuration.md) | `ezra.yaml`, env vars, models directory |
| [CLI reference](cli.md) | Full command list and common flags (`models recommend`, `agents`, …) |

Sphinx entrypoints (also published as HTML - see **Publish** below):

| File | Role |
|------|------|
| [`index.rst`](index.rst) | Site home + toctree |
| [`api.rst`](api.rst) | Autodoc API reference |
| [`conf.py`](conf.py) | Sphinx / MyST / Furo theme config |
| [`Makefile`](Makefile) / [`make.bat`](make.bat) | Local HTML builds |

## Build the HTML docs (local)

```bash
pip install -e ".[docs]"
cd docs
make html          # Linux / macOS
# Windows: .\make.bat html
```

Then open `_build/html/index.html`.

## Publish (so people get a link)

This repo ships two ways to host the same Sphinx site:

### 1. GitHub Pages (recommended, already wired)

1. Push `.github/workflows/docs.yml` to `main`.
2. Repo **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. After the **Docs** workflow succeeds, the site is at:
   **https://awwal41.github.io/EZRA/**
4. Optional: GitHub repo **About → Website** → paste that URL (shows on the repo front page).

PRs that touch `docs/` or `src/ezra/` also run a docs build so broken Sphinx does not merge unnoticed.

### 2. Read the Docs (optional mirror)

Config is already in [`.readthedocs.yaml`](../.readthedocs.yaml).

1. Sign in at [readthedocs.org](https://readthedocs.org/) with GitHub.
2. **Import a project** → choose `Awwal41/EZRA`.
3. Set the project name to `ezra` (URL becomes `https://ezra.readthedocs.io/` if available).
4. Trigger a build; RTD uses `.readthedocs.yaml` + `docs/conf.py` automatically.

**Contributing** (dev setup, gallery PRs, style): see [CONTRIBUTING.md](../CONTRIBUTING.md).

**Roadmap / backlog:** [TODO.md](../TODO.md).
