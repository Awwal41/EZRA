"""Cline integration — coding-agent CLI / SDK for EZRA (optional).

Upstream sources are a **full in-tree snapshot** at ``third_party/Cline/``
([cline/cline](https://github.com/cline/cline), Apache-2.0) — not a
submodule — so EZRA keeps the code even if upstream goes away. See
``third_party/Cline/UPSTREAM.txt``.

This package is a thin, safe facade:

- Locates the vendored tree / CLI
- Reports availability for ``ezra doctor``
- Does **not** auto-run the agent, start Kanban, or install IDE extensions

Prefer importing from here instead of the TypeScript tree under
``third_party/Cline/``.

Typical usage::

    from ezra.cline import cline_available, cline_root, resolve_cli

    if cline_available():
        print(cline_root(), resolve_cli())
"""

from __future__ import annotations

from ezra.cline.cli import (
    ClineNotAvailable,
    cline_available,
    cline_version,
    resolve_cli,
    run_cline,
)
from ezra.cline.paths import cline_pin_info, cline_root

__all__ = [
    "ClineNotAvailable",
    "cline_available",
    "cline_pin_info",
    "cline_root",
    "cline_version",
    "resolve_cli",
    "run_cline",
]
