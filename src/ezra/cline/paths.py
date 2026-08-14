"""Locate the vendored Cline source tree (full in-tree snapshot)."""

from __future__ import annotations

import os
from pathlib import Path


def cline_root() -> Path | None:
    """Return ``third_party/Cline`` when present in this EZRA checkout.

    This is a **full vendored copy** of Cline sources (not a git submodule),
    so EZRA keeps working offline even if upstream vanishes.

    Override with ``EZRA_CLINE_ROOT`` (absolute path to a Cline tree).
    """
    env = os.environ.get("EZRA_CLINE_ROOT", "").strip()
    if env:
        path = Path(env).expanduser().resolve()
        return path if path.is_dir() else None

    from ezra.hpc.sites import repo_root

    candidate = repo_root() / "third_party" / "Cline"
    if candidate.is_dir() and (candidate / "package.json").is_file():
        return candidate.resolve()
    return None


def cline_pin_info(root: Path | None = None) -> dict[str, str]:
    """Best-effort version / pin metadata from the checkout (no network)."""
    root = root if root is not None else cline_root()
    info: dict[str, str] = {
        "upstream": "https://github.com/cline/cline",
        "license": "Apache-2.0",
    }
    if root is None:
        return info
    info["root"] = str(root)
    pkg = root / "apps" / "cli" / "package.json"
    if pkg.is_file():
        try:
            import json

            data = json.loads(pkg.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("version"):
                info["version"] = str(data["version"])
        except (OSError, ValueError, TypeError):
            pass
    return info
