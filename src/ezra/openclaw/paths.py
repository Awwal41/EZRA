"""Locate the OpenClaw submodule checkout."""

from __future__ import annotations

import os
from pathlib import Path


def openclaw_root() -> Path | None:
    """Return ``third_party/OpenClaw`` when present in this EZRA checkout.

    Override with ``EZRA_OPENCLAW_ROOT`` (absolute path to an OpenClaw tree).
    """
    env = os.environ.get("EZRA_OPENCLAW_ROOT", "").strip()
    if env:
        path = Path(env).expanduser().resolve()
        return path if path.is_dir() else None

    from ezra.hpc.sites import repo_root

    candidate = repo_root() / "third_party" / "OpenClaw"
    if candidate.is_dir() and (candidate / "package.json").is_file():
        return candidate.resolve()
    return None


def openclaw_pin_info(root: Path | None = None) -> dict[str, str]:
    """Best-effort version / pin metadata from the checkout (no network)."""
    root = root if root is not None else openclaw_root()
    info: dict[str, str] = {
        "upstream": "https://github.com/openclaw/openclaw",
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
    return info
