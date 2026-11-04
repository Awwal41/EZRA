"""Tests for ezra.peekaboo path helpers (no macOS CLI required)."""

from __future__ import annotations

import platform
from pathlib import Path

import pytest

from ezra.config import load_config
from ezra.peekaboo import (
    mcp_launch_command,
    peekaboo_platform_supported,
    peekaboo_root,
    resolve_cli,
)


@pytest.mark.skipif(
    peekaboo_root() is None,
    reason="third_party/Peekaboo not fetched — run scripts/fetch_third_party.py",
)
def test_peekaboo_root_points_at_vendored_tree() -> None:
    root = peekaboo_root()
    assert root is not None
    assert root.name == "Peekaboo"
    assert (root / "README.md").is_file()
    assert (root / "UPSTREAM.txt").is_file()


def test_platform_flag_matches_system() -> None:
    assert peekaboo_platform_supported() is (platform.system() == "Darwin")


def test_mcp_launch_command_shape() -> None:
    argv = mcp_launch_command(prefer_npx=True)
    assert len(argv) >= 2
    assert argv[-1] == "mcp"
    assert "peekaboo" in " ".join(argv).lower()


def test_resolve_cli_override(monkeypatch, tmp_path: Path) -> None:
    fake = tmp_path / "peekaboo"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setenv("EZRA_PEEKABOO_CLI", str(fake))
    assert resolve_cli() == fake.resolve()


def test_config_peekaboo_defaults() -> None:
    cfg = load_config()
    assert cfg.peekaboo_enabled == "auto"
