"""Resolve and (optionally) invoke the Cline CLI from EZRA.

Safety: helpers only locate / probe the CLI. They do **not** start an agent
session, Kanban board, or IDE extension. Callers must opt in explicitly via
:func:`run_cline`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from ezra.cline.paths import cline_root


class ClineNotAvailable(RuntimeError):
    """Raised when the Cline CLI cannot be resolved."""


def resolve_cli() -> Path | None:
    """Locate a ``cline`` executable or vendored entrypoint.

    Precedence:

    1. ``EZRA_CLINE_CLI`` / config override via env
    2. ``cline`` on ``PATH`` (e.g. ``npm i -g cline``)
    3. Built ``apps/cli/dist/index.js`` under ``third_party/Cline/``
    4. Source ``apps/cli/src/index.ts`` (needs Bun)
    """
    env = os.environ.get("EZRA_CLINE_CLI", "").strip()
    if env:
        path = Path(env).expanduser().resolve()
        return path if path.is_file() else None

    which = shutil.which("cline")
    if which:
        return Path(which).resolve()

    root = cline_root()
    if root is None:
        return None

    for candidate in (
        root / "apps" / "cli" / "dist" / "index.js",
        root / "apps" / "cli" / "src" / "index.ts",
    ):
        if candidate.is_file():
            return candidate.resolve()
    return None


def cline_available() -> bool:
    """True if a CLI binary/entry or vendored checkout is present."""
    if resolve_cli() is not None:
        return True
    return cline_root() is not None


def run_cline(
    *args: str,
    check: bool = True,
    capture_output: bool = True,
    timeout: float | None = 60.0,
) -> subprocess.CompletedProcess[str]:
    """Run ``cline <args>`` (or ``bun`` / ``node`` on the vendored entry).

    Does not start background agent sessions. Prefer read-only probes such as
    ``--version`` from the EZRA CLI wrappers.
    """
    cli = resolve_cli()
    if cli is None:
        root = cline_root()
        hint = (
            f"Vendored sources are at {root}. Install Node 22+ / Bun 1.3+ and "
            "either `npm i -g cline` or build the vendored tree "
            "(see third_party/Cline/README.md)."
            if root
            else "Install: npm i -g cline  "
            "(or restore third_party/Cline from the EZRA repo)"
        )
        raise ClineNotAvailable(f"Cline CLI not found. {hint}")

    suffix = cli.suffix.lower()
    if suffix == ".ts":
        bun = shutil.which("bun")
        if not bun:
            raise ClineNotAvailable(
                f"Found {cli} but `bun` is not on PATH. "
                "Install Bun 1.3+ (see third_party/Cline/README.md) "
                "or `npm i -g cline`."
            )
        cmd = [bun, str(cli), *args]
    elif suffix in {".js", ".mjs", ".cjs"}:
        node = shutil.which("node")
        if not node:
            raise ClineNotAvailable(
                f"Found {cli} but `node` is not on PATH. "
                "Install Node.js 22+ or `npm i -g cline`."
            )
        cmd = [node, str(cli), *args]
    else:
        cmd = [str(cli), *args]

    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture_output,
        text=True,
        timeout=timeout,
    )


def cline_version() -> str | None:
    """Return ``cline --version`` output, or None if unavailable."""
    try:
        proc = run_cline("--version", check=False, timeout=30.0)
    except (ClineNotAvailable, OSError, subprocess.TimeoutExpired):
        return None
    text = (proc.stdout or proc.stderr or "").strip()
    return text or None
