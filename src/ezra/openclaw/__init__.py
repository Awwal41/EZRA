"""OpenClaw integration — personal AI gateway for EZRA agents (optional).

Upstream lives as a **git submodule** at ``third_party/OpenClaw/``
([openclaw/openclaw](https://github.com/openclaw/openclaw), MIT), pinned to a
release tag (see ``third_party/README.md``).

This package is a thin, safe facade:

- Locates the submodule / CLI
- Reports availability for ``ezra doctor``
- Does **not** auto-run ``onboard``, install daemons, or expose the Gateway

Prefer importing from here instead of the TypeScript tree under
``third_party/OpenClaw/``.

Typical usage::

    from ezra.openclaw import openclaw_available, openclaw_root, resolve_cli

    if openclaw_available():
        print(openclaw_root(), resolve_cli())
"""

from __future__ import annotations

from ezra.openclaw.cli import (
    OpenClawNotAvailable,
    openclaw_available,
    openclaw_version,
    resolve_cli,
    run_openclaw,
)
from ezra.openclaw.paths import openclaw_pin_info, openclaw_root

__all__ = [
    "OpenClawNotAvailable",
    "openclaw_available",
    "openclaw_pin_info",
    "openclaw_root",
    "openclaw_version",
    "resolve_cli",
    "run_openclaw",
]
