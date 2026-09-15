"""Locate the vendored Voicebox source tree (full in-tree snapshot)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 17493


def voicebox_root() -> Path | None:
    """Return ``third_party/Voicebox`` when present in this EZRA checkout.

    This is a **full vendored copy** of Voicebox sources (not a git submodule),
    so EZRA keeps working offline even if upstream vanishes.

    Override with ``EZRA_VOICEBOX_ROOT`` (absolute path to a Voicebox tree).
    """
    env = os.environ.get("EZRA_VOICEBOX_ROOT", "").strip()
    if env:
        path = Path(env).expanduser().resolve()
        return path if path.is_dir() else None

    from ezra.hpc.sites import repo_root

    candidate = repo_root() / "third_party" / "Voicebox"
    if candidate.is_dir() and (candidate / "package.json").is_file():
        return candidate.resolve()
    return None


def voicebox_pin_info(root: Path | None = None) -> dict[str, str]:
    """Best-effort version / pin metadata from the checkout (no network)."""
    root = root if root is not None else voicebox_root()
    info: dict[str, str] = {
        "upstream": "https://github.com/jamiepine/voicebox",
        "license": "MIT",
    }
    if root is None:
        return info
    info["root"] = str(root)
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            import json

            data = json.loads(pkg.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("version"):
                info["version"] = str(data["version"])
        except (OSError, ValueError, TypeError):
            pass
    upstream = root / "UPSTREAM.txt"
    if upstream.is_file():
        try:
            for line in upstream.read_text(encoding="utf-8").splitlines():
                if line.lower().startswith("snapshot commit:"):
                    info["snapshot"] = line.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
    return info


def resolve_mcp_shim() -> Path | None:
    """Locate a ``voicebox-mcp`` stdio shim binary when present.

    Precedence:

    1. ``EZRA_VOICEBOX_MCP``
    2. ``voicebox-mcp`` / ``voicebox-mcp.exe`` on ``PATH``
    3. Common build outputs under ``third_party/Voicebox/``
    """
    env = os.environ.get("EZRA_VOICEBOX_MCP", "").strip()
    if env:
        path = Path(env).expanduser().resolve()
        return path if path.is_file() else None

    which = shutil.which("voicebox-mcp")
    if which:
        return Path(which).resolve()

    root = voicebox_root()
    if root is None:
        return None

    exe = "voicebox-mcp.exe" if os.name == "nt" else "voicebox-mcp"
    candidates = [
        root / "tauri" / "src-tauri" / "binaries" / exe,
        root / "tauri" / "src-tauri" / "binaries" / "voicebox-mcp",
        root / "bin" / exe,
        root / "dist" / exe,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None
