"""Locate the vendored gogcli tree and MCP launch command."""

from __future__ import annotations

import os
from pathlib import Path


def gog_root() -> Path | None:
    """Return ``third_party/gogcli`` when present in this EZRA checkout.

    Full in-tree snapshot (not a git submodule). Override with ``EZRA_GOG_ROOT``.
    """
    env = os.environ.get("EZRA_GOG_ROOT", "").strip()
    if env:
        path = Path(env).expanduser().resolve()
        return path if path.is_dir() else None

    from ezra.hpc.sites import repo_root

    candidate = repo_root() / "third_party" / "gogcli"
    if candidate.is_dir() and (candidate / "README.md").is_file():
        return candidate.resolve()
    return None


def mcp_launch_command() -> list[str]:
    """Return an argv suitable for MCP client config (``gog mcp``, stdio)."""
    from ezra.gog.cli import resolve_cli

    cli = resolve_cli()
    if cli is not None:
        return [str(cli), "mcp"]
    return ["gog", "mcp"]
