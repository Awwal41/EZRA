"""Locate the vendored Peekaboo tree and MCP launch command."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def peekaboo_root() -> Path | None:
    """Return ``third_party/Peekaboo`` when present in this EZRA checkout.

    Full in-tree snapshot (not a git submodule). Override with
    ``EZRA_PEEKABOO_ROOT``.
    """
    env = os.environ.get("EZRA_PEEKABOO_ROOT", "").strip()
    if env:
        path = Path(env).expanduser().resolve()
        return path if path.is_dir() else None

    from ezra.hpc.sites import repo_root

    candidate = repo_root() / "third_party" / "Peekaboo"
    if candidate.is_dir() and (candidate / "README.md").is_file():
        return candidate.resolve()
    return None


def mcp_launch_command(*, prefer_npx: bool = False) -> list[str]:
    """Return an argv suitable for MCP client config (stdio server).

    Prefer a resolved local ``peekaboo`` binary; fall back to the published
    npm package ``@steipete/peekaboo`` via ``npx`` when ``prefer_npx`` is true
    or no local binary is found.
    """
    from ezra.peekaboo.cli import resolve_cli

    cli = resolve_cli()
    if cli is not None and not prefer_npx:
        return [str(cli), "mcp"]
    npx = shutil.which("npx")
    if npx:
        return [npx, "-y", "@steipete/peekaboo", "mcp"]
    if cli is not None:
        return [str(cli), "mcp"]
    return ["npx", "-y", "@steipete/peekaboo", "mcp"]
