# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

# Package import path for autodoc
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ezra import __version__  # noqa: E402

project = "EZRA"
author = "EZRA Contributors"
copyright = f"{datetime.now().year}, {author}"
release = __version__
version = ".".join(release.split(".")[:2])

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "README.md"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

root_doc = "index"

html_theme = "furo"
html_static_path = ["_static"]
html_title = f"EZRA {release}"
html_logo = "_static/logo-icon-light.svg"
html_favicon = "_static/favicon.svg"

# Classic Read the Docs blue for sidebar + brand (links, accents)
_RTD_BLUE = "#2980B9"
_RTD_BLUE_HOVER = "#3091d1"
_RTD_BLUE_DARK = "#2472a4"
_RTD_BLUE_LIGHT = "#5dade2"

html_theme_options = {
    # Light-ink mark: readable on blue sidebar (light) and dark sidebar (dark)
    "light_logo": "logo-icon-light.svg",
    "dark_logo": "logo-icon-light.svg",
    "sidebar_hide_name": False,
    "source_repository": "https://github.com/Awwal41/EZRA",
    "source_branch": "main",
    "source_directory": "docs/",
    "light_css_variables": {
        "color-brand-primary": _RTD_BLUE,
        "color-brand-content": _RTD_BLUE,
        "color-sidebar-background": _RTD_BLUE,
        "color-sidebar-background-border": _RTD_BLUE,
        "color-sidebar-brand-text": "#ffffff",
        "color-sidebar-caption-text": "#e8f4fc",
        "color-sidebar-link-text": "#ffffff",
        "color-sidebar-link-text--top-level": "#ffffff",
        "color-sidebar-item-background--hover": _RTD_BLUE_HOVER,
        "color-sidebar-item-background--current": _RTD_BLUE_HOVER,
        "color-sidebar-item-expander-background--hover": _RTD_BLUE_HOVER,
        "color-sidebar-search-background": _RTD_BLUE_DARK,
        "color-sidebar-search-background--focus": _RTD_BLUE_DARK,
        "color-sidebar-search-border": _RTD_BLUE_DARK,
        "color-sidebar-search-text": "#ffffff",
        "color-sidebar-search-foreground": "#ffffff",
        "color-sidebar-search-icon": "#ffffff",
    },
    "dark_css_variables": {
        "color-brand-primary": _RTD_BLUE_LIGHT,
        "color-brand-content": _RTD_BLUE_LIGHT,
        # Keep dark sidebar dark (light-mode blue would otherwise inherit)
        "color-sidebar-background": "#131416",
        "color-sidebar-background-border": "#303335",
        "color-sidebar-brand-text": "#ffffff",
        "color-sidebar-caption-text": "#8b8b8d",
        "color-sidebar-link-text": "#d0d0d0",
        "color-sidebar-link-text--top-level": "#ffffff",
        "color-sidebar-item-background--hover": "#1a1c1e",
        "color-sidebar-item-background--current": "#1a1c1e",
        "color-sidebar-item-expander-background--hover": "#1a1c1e",
        "color-sidebar-search-background": "#202020",
        "color-sidebar-search-background--focus": "#202020",
        "color-sidebar-search-border": "#303335",
        "color-sidebar-search-text": "#d0d0d0",
        "color-sidebar-search-foreground": "#d0d0d0",
        "color-sidebar-search-icon": "#8b8b8d",
    },
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/Awwal41/EZRA",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38
                    0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52
                    -.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2
                    -3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64
                    -.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08
                    2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01
                    1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3

autodoc_typehints = "description"
autodoc_member_order = "bysource"
autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# Quiet common GitHub-relative links that resolve on the repo, not in HTML builds
linkcheck_ignore = [
    r"https://github.com/YOUR_USER/.*",
]
