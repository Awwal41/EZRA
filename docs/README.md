# EZRA documentation

Guides live here as **Markdown** (easy to read on GitHub) and are built into an
HTML site with **Sphinx** + **MyST** + **reStructuredText**.

| Guide | When to read it |
|-------|-----------------|
| [Installation](install.md) | First-time setup (venv, `pip install`, `ezra doctor`) |
| [Models](models.md) | Recommend by hardware + keyword, browse, download, status, remove |
| [Personal agents](agents.md) | Scaffold your own assistant (prompt + preferred models) |
| [Conversation runtime](conversation.md) | Sessions, `ezra chat` / `serve`, OpenAI `/v1` |
| [Document parsing](parse.md) | MegaParse + basic backends, `ezra parse`, chat `--file` |
| [OpenClaw](openclaw.md) | Full in-tree snapshot + `ezra.openclaw` (Gateway optional; no auto-start) |
| [HPC / SLURM](hpc.md) | Site profiles, scratch paths, SBATCH submit |
| [Site profiles](sites.md) | Customize partition/modules for your cluster ([full notes](../sites/README.md)) |
| [Configuration](configuration.md) | `ezra.yaml`, env vars, models directory |
| [Peekaboo](peekaboo.md) | macOS screen capture / UI automation (vendored) + MCP |
| [gogcli](gog.md) | Google Workspace CLI (`gog`, vendored) + MCP |
| [CLI reference](cli.md) | Full command list and common flags (`models recommend`, `agents`, …) |

Sphinx entrypoints (also published as HTML - see **Publish** below):

| File | Role |
|------|------|
| [`index.rst`](index.rst) | Site home + toctree |
| [`api.rst`](api.rst) | Autodoc API reference |
| [`changelog.rst`](changelog.rst) | Release notes |
| [`contributing.rst`](contributing.rst) | Contributor pointer into `CONTRIBUTING.md` |
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

### Prebuilt HTML in the repo (interim)

Until Vercel / Pages is fully set up, a compiled copy lives at
[`site/index.html`](../site/index.html). Clone the repo and open that file in a
browser — no Sphinx install required. Regenerate with
`python -m sphinx -b html docs site` (then delete `site/.doctrees`).

## Publish (so people get a link)

This repo ships three ways to host the same Sphinx site. For a **private** GitHub
repo, prefer **Vercel** (or GitHub Pages) so collaborators get a URL without
making the source public. A Vercel URL is public by default — turn on
**Deployment Protection** if only your team should open the docs.

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

### 3. Vercel (optional shareable URL)

Works with a **private** GitHub repo. Sphinx is built in GitHub Actions
([`.github/workflows/docs-vercel.yml`](../.github/workflows/docs-vercel.yml)), then
the HTML is uploaded to Vercel. Root [`vercel.json`](../vercel.json) is for a
Git-connected Vercel project (native install/build) if you prefer that path.

**One-time setup**

1. At [vercel.com](https://vercel.com/), import the private EZRA repo (grant the
   Vercel GitHub App access to the repo), or run `npx vercel` once from a clone
   to create the project.
2. In the Vercel project: **Settings → General** — copy **Project ID** and
   **Team/Org ID**.
3. Create a token: [vercel.com/account/tokens](https://vercel.com/account/tokens).
4. In GitHub: repo **Settings → Secrets and variables → Actions** — add:
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`
5. Optional (recommended for private docs): Vercel project → **Deployment
   Protection** → require Vercel Authentication (team) or a password.
6. Push to `main` (paths under `docs/` / `src/ezra/`) or run **Actions → Docs
   (Vercel) → Run workflow**. The job no-ops with a notice until the three
   secrets exist.

Share the production URL from the Vercel dashboard (or the deploy step logs)
with collaborators.

**Contributing** (dev setup, gallery PRs, style): see [CONTRIBUTING.md](../CONTRIBUTING.md).

**Roadmap / backlog:** [TODO.md](../TODO.md).
