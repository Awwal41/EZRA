"""Resolve and invoke the ``gog`` CLI from EZRA."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from ezra.gog.paths import gog_root


class GogNotAvailable(RuntimeError):
    """Raised when the gog CLI cannot be found or executed."""


def resolve_cli() -> Path | None:
    """Locate a ``gog`` executable.

    Precedence:

    1. ``EZRA_GOG_CLI``
    2. ``gog`` on ``PATH``
    3. Common build outputs under ``third_party/gogcli/``
    """
    env = os.environ.get("EZRA_GOG_CLI", "").strip()
    if env:
        path = Path(env).expanduser().resolve()
        return path if path.is_file() else None

    which = shutil.which("gog")
    if which:
        return Path(which).resolve()

    root = gog_root()
    if root is None:
        return None

    exe = "gog.exe" if os.name == "nt" else "gog"
    candidates = [
        root / "bin" / exe,
        root / "dist" / exe,
        root / exe,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def gog_available() -> bool:
    """True if a ``gog`` binary is on PATH or built under the submodule."""
    if resolve_cli() is not None:
        return True
    return gog_root() is not None


def run_gog(
    *args: str,
    check: bool = True,
    capture_output: bool = True,
    timeout: float | None = 120.0,
    readonly: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run ``gog <args>`` and return the completed process.

    When ``readonly`` is true, prepends ``--readonly`` (safe default for agents).
    """
    cli = resolve_cli()
    if cli is None:
        root = gog_root()
        hint = (
            f"Vendored sources are at {root}. Build with ``make build`` "
            "(see third_party/gogcli/README.md) or: brew install openclaw/tap/gogcli"
            if root
            else "Install: brew install openclaw/tap/gogcli  "
            "(or clone submodule + make build)"
        )
        raise GogNotAvailable(
            "gog CLI not found on PATH and no built binary under "
            f"third_party/gogcli/. {hint}"
        )
    argv = [str(cli)]
    if readonly:
        argv.append("--readonly")
    argv.extend(args)
    return subprocess.run(
        argv,
        check=check,
        capture_output=capture_output,
        text=True,
        timeout=timeout,
    )
