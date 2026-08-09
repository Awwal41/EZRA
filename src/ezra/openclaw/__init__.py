"""OpenClaw integration — personal AI gateway for EZRA agents (optional).

Upstream sources are a **full in-tree snapshot** at ``third_party/OpenClaw/``
([openclaw/openclaw](https://github.com/openclaw/openclaw), MIT) — not a
submodule — so EZRA keeps the code even if upstream goes away. See
``third_party/OpenClaw/UPSTREAM.txt``.

This package is a thin, safe facade:

- Locates the vendored tree / CLI
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
