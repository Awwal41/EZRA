# Prebuilt EZRA docs (HTML)

Compiled Sphinx site for collaborators who do not want to wait on Vercel / GitHub Pages.

**Open locally:** double-click [`index.html`](index.html) (or open it from your editor / browser after cloning).

Regenerate from the repo root (after `pip install -e ".[docs]"`):

```bash
python -m sphinx -b html docs site
# remove Sphinx cache from the published tree
rm -rf site/.doctrees
```

This folder is a **snapshot**. Prefer live hosting when available: GitHub Pages, Read the Docs, or Vercel — see [`docs/README.md`](../docs/README.md#publish-so-people-get-a-link).
