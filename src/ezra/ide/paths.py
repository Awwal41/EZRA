"""Locate the in-tree VS Code / Cursor extension sources."""

from __future__ import annotations

from pathlib import Path

PUBLISHER = "ezra-local"
EXTENSION_NAME = "ezra-grid"
EXTENSION_ID = f"{PUBLISHER}.{EXTENSION_NAME}"


def extension_root() -> Path | None:
    """Return ``ide/vscode`` when present in this EZRA checkout."""
    from ezra.hpc.sites import repo_root

    candidate = repo_root() / "ide" / "vscode"
    if candidate.is_dir() and (candidate / "package.json").is_file():
        return candidate.resolve()
    return None


def extension_folder_name(version: str) -> str:
    """On-disk folder name used by VS Code / Cursor after sideload."""
    return f"{PUBLISHER}.{EXTENSION_NAME}-{version}"
