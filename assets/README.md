# EZRA brand assets

SVG logos: a **rising structure** from a broken base, with the final keystone being
placed - rebuilding in progress (inspired by biblical Ezra the restorer).

| File | Ink | Use |
|------|-----|-----|
| [`logo-icon.svg`](logo-icon.svg) | Dark (`#1a1a1a`) | App icon on light backgrounds |
| [`logo-icon-light.svg`](logo-icon-light.svg) | Light (`#ffffff`) | Icon on dark or colored backgrounds |
| [`logo.svg`](logo.svg) | Dark | README / headers (light mode) |
| [`logo-light.svg`](logo-light.svg) | Light | README / headers (dark mode) |

## Symbol

- **Broken base**: incomplete foundation
- **Rising columns** of different heights: rebuilding underway
- **Upper beam**: structure coming together
- **Keystone**: the final stone being set

## Where copies live

- Canonical sources: this folder (`assets/`)
- Sphinx / GitHub Pages / RTD: [`docs/_static/`](../docs/_static/)
  - Sidebar uses the **light-ink** icon (blue sidebar in light mode, dark sidebar in dark mode)
  - Favicon: light mark on RTD blue (`#2980B9`) badge
- README: `<picture>` switches `logo.svg` / `logo-light.svg` with `prefers-color-scheme`
