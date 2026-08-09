"""Peekaboo integration — macOS screen capture / UI automation for EZRA agents.

Upstream lives as a git submodule at ``third_party/Peekaboo/``
([openclaw/Peekaboo](https://github.com/openclaw/Peekaboo), MIT).

Peekaboo is **macOS-only**. On other platforms helpers report unavailable and
CLI wrappers raise a clear error. Prefer this package over calling the vendor
tree directly so agents, doctor, and MCP config share one resolution path.

Typical usage::

    from ezra.peekaboo import peekaboo_available, resolve_cli, capture_screen

    if peekaboo_available():
        path = capture_screen()  # → ~/.ezra/captures/...
"""

from __future__ import annotations

from ezra.peekaboo.cli import (
    PeekabooNotAvailable,
    capture_screen,
    peekaboo_available,
    peekaboo_platform_supported,
    resolve_cli,
    run_peekaboo,
)
from ezra.peekaboo.paths import mcp_launch_command, peekaboo_root

__all__ = [
    "PeekabooNotAvailable",
    "capture_screen",
    "mcp_launch_command",
    "peekaboo_available",
    "peekaboo_platform_supported",
    "peekaboo_root",
    "resolve_cli",
    "run_peekaboo",
]
