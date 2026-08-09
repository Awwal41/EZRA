"""gogcli integration — Google Workspace CLI for EZRA agents.

Upstream is a **full in-tree snapshot** at ``third_party/gogcli/``
([openclaw/gogcli](https://github.com/openclaw/gogcli), MIT).

The binary is ``gog`` (Gmail, Calendar, Drive, Docs, Sheets, …) with an
optional read-only-by-default MCP server via ``gog mcp``. Prefer this package
over calling the vendor tree directly.

Typical usage::

    from ezra.gog import gog_available, resolve_cli, run_gog

    if gog_available():
        result = run_gog("--readonly", "gmail", "search", "newer_than:7d", "--json")
"""

from __future__ import annotations

from ezra.gog.cli import (
    GogNotAvailable,
    gog_available,
    resolve_cli,
    run_gog,
)
from ezra.gog.paths import gog_root, mcp_launch_command

__all__ = [
    "GogNotAvailable",
    "gog_available",
    "gog_root",
    "mcp_launch_command",
    "resolve_cli",
    "run_gog",
]
