"""Resolve and invoke the Peekaboo CLI from EZRA."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from ezra.config import default_home
from ezra.peekaboo.paths import peekaboo_root


class PeekabooNotAvailable(RuntimeError):
    """Raised when Peekaboo cannot run on this machine / checkout."""


def peekaboo_platform_supported() -> bool:
    """True on macOS (Peekaboo's only supported host OS)."""
    return platform.system() == "Darwin"


def resolve_cli() -> Path | None:
    """Locate a ``peekaboo`` executable.

    Precedence:

    1. ``EZRA_PEEKABOO_CLI`` / config override via env
    2. ``peekaboo`` on ``PATH``
    3. Common build outputs under ``third_party/Peekaboo/``
    """
    env = os.environ.get("EZRA_PEEKABOO_CLI", "").strip()
    if env:
        path = Path(env).expanduser().resolve()
        return path if path.is_file() else None

    which = shutil.which("peekaboo")
    if which:
        return Path(which).resolve()

    root = peekaboo_root()
    if root is None:
        return None

    candidates = [
        root / ".build" / "release" / "peekaboo",
        root / ".build" / "debug" / "peekaboo",
        root / "release" / "peekaboo",
        root / "Apps" / "CLI" / ".build" / "release" / "peekaboo",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def peekaboo_available() -> bool:
    """True if this host can run Peekaboo (macOS + CLI or vendored tree)."""
    if not peekaboo_platform_supported():
        return False
    if resolve_cli() is not None:
        return True
    # Source tree present — usable after `pnpm run build:cli` / brew install
    return peekaboo_root() is not None


def run_peekaboo(
    *args: str,
    check: bool = True,
    capture_output: bool = True,
    timeout: float | None = 120.0,
) -> subprocess.CompletedProcess[str]:
    """Run ``peekaboo <args>`` and return the completed process."""
    if not peekaboo_platform_supported():
        raise PeekabooNotAvailable(
            "Peekaboo is macOS-only. On Windows/Linux use PeekabooWin / PeekabooX "
            "community ports, or run capture on a Mac host. "
            "See https://github.com/openclaw/Peekaboo"
        )
    cli = resolve_cli()
    if cli is None:
        root = peekaboo_root()
        hint = (
            f"Vendored sources are at {root}. Build with pnpm (see third_party/Peekaboo/README.md) "
            "or: brew install steipete/tap/peekaboo"
            if root
            else "Install: brew install steipete/tap/peekaboo  (or clone submodule + build)"
        )
        raise PeekabooNotAvailable(
            "Peekaboo CLI not found on PATH and no built binary under "
            f"third_party/Peekaboo/. {hint}"
        )
    return subprocess.run(
        [str(cli), *args],
        check=check,
        capture_output=capture_output,
        text=True,
        timeout=timeout,
    )


def capture_screen(
    path: Path | str | None = None,
    *,
    mode: str = "screen",
) -> Path:
    """Capture the screen (or window) via ``peekaboo image``.

    Defaults to ``~/.ezra/captures/peekaboo-<timestamp>.png``.
    """
    if path is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = default_home() / "captures" / f"peekaboo-{stamp}.png"
    else:
        out = Path(path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    run_peekaboo("image", "--mode", mode, "--path", str(out.resolve()))
    return out.resolve()
