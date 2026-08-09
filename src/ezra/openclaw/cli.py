"""Resolve and (optionally) invoke the OpenClaw CLI from EZRA.

Safety: helpers only locate / probe the CLI. They do **not** run
``openclaw onboard``, start the Gateway, or install daemons. Callers must
opt in explicitly via :func:`run_openclaw`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from ezra.openclaw.paths import openclaw_root


class OpenClawNotAvailable(RuntimeError):
    """Raised when the OpenClaw CLI cannot be resolved."""


def resolve_cli() -> Path | None:
    """Locate an ``openclaw`` executable.

    Precedence:

    1. ``EZRA_OPENCLAW_CLI`` / config override via env
    2. ``openclaw`` on ``PATH`` (e.g. ``npm install -g openclaw``)
    3. ``openclaw.mjs`` under ``third_party/OpenClaw/`` (needs Node)
    """
    env = os.environ.get("EZRA_OPENCLAW_CLI", "").strip()
    if env:
        path = Path(env).expanduser().resolve()
        return path if path.is_file() else None

    which = shutil.which("openclaw")
    if which:
        return Path(which).resolve()

    root = openclaw_root()
    if root is None:
        return None

    for candidate in (
        root / "openclaw.mjs",
        root / "dist" / "openclaw.mjs",
    ):
        if candidate.is_file():
            return candidate.resolve()
    return None


def openclaw_available() -> bool:
    """True if a CLI binary/entry or vendored checkout is present."""
    if resolve_cli() is not None:
        return True
    return openclaw_root() is not None


def run_openclaw(
    *args: str,
    check: bool = True,
    capture_output: bool = True,
    timeout: float | None = 60.0,
) -> subprocess.CompletedProcess[str]:
    """Run ``openclaw <args>`` (or ``node openclaw.mjs <args>``).

    Does not start background services. Prefer read-only probes such as
    ``--version`` / ``gateway status`` from the EZRA CLI wrappers.
    """
    cli = resolve_cli()
    if cli is None:
        root = openclaw_root()
        hint = (
            f"Vendored sources are at {root}. Install Node 22+ and either "
            "`npm install -g openclaw@latest` or build the submodule "
            "(see third_party/OpenClaw/README.md)."
            if root
            else "Install: npm install -g openclaw@latest  "
            "(or: git submodule update --init third_party/OpenClaw)"
        )
        raise OpenClawNotAvailable(f"OpenClaw CLI not found. {hint}")

    if cli.suffix.lower() == ".mjs":
        node = shutil.which("node")
        if not node:
            raise OpenClawNotAvailable(
                f"Found {cli} but `node` is not on PATH. "
                "Install Node.js 22+ (see https://docs.openclaw.ai)."
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


def openclaw_version() -> str | None:
    """Return ``openclaw --version`` output, or None if unavailable."""
    try:
        proc = run_openclaw("--version", check=False, timeout=30.0)
    except (OpenClawNotAvailable, OSError, subprocess.TimeoutExpired):
        return None
    text = (proc.stdout or proc.stderr or "").strip()
    return text or None
