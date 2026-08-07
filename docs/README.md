# EZRA documentation

Guides live here as **Markdown** (easy to read on GitHub) and are built into an
HTML site with **Sphinx** + **MyST** + **reStructuredText**.

| Guide | When to read it |
|-------|-----------------|
| [Installation](install.md) | First-time setup (venv, `pip install`, `ezra doctor`) |
| [Models](models.md) | Recommend by hardware + keyword, browse, download, status, remove |
| [HPC / SLURM](hpc.md) | Site profiles, scratch paths, SBATCH submit |
| [Site profiles](sites.md) | Customize partition/modules for your cluster ([full notes](../sites/README.md)) |
| [Configuration](configuration.md) | `ezra.yaml`, env vars, models directory |
| [CLI reference](cli.md) | Full command list and common flags (`models recommend`, …) |

Sphinx entrypoints (also on [Read the Docs](https://ezra.readthedocs.io) once linked):

| File | Role |
|------|------|
| [`index.rst`](index.rst) | Site home + toctree |
| [`api.rst`](api.rst) | Autodoc API reference |
| [`conf.py`](conf.py) | Sphinx / MyST / Furo theme config |
| [`Makefile`](Makefile) / [`make.bat`](make.bat) | Local HTML builds |

## Build the HTML docs

```bash
pip install -e ".[docs]"
cd docs
make html          # Linux / macOS
# Windows: .\make.bat html
```

Then open `_build/html/index.html`.

**Contributing** (dev setup, gallery PRs, style): see [CONTRIBUTING.md](../CONTRIBUTING.md).

**Roadmap / backlog:** [TODO.md](../TODO.md).
