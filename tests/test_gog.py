"""Tests for ezra.gog path helpers (no Google auth required)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ezra.config import load_config
from ezra.gog import gog_root, mcp_launch_command, resolve_cli


@pytest.mark.skipif(
    gog_root() is None, reason="third_party/gogcli not fetched — run scripts/fetch_third_party.py"
)
def test_gog_root_points_at_vendored_tree() -> None:
    root = gog_root()
    assert root is not None
    assert root.name == "gogcli"
    assert (root / "README.md").is_file()
    assert (root / "go.mod").is_file()
    assert (root / "UPSTREAM.txt").is_file()


def test_mcp_launch_command_shape() -> None:
    argv = mcp_launch_command()
    assert len(argv) >= 2
    assert argv[-1] == "mcp"
    assert "gog" in Path(argv[0]).name.lower() or argv[0] == "gog"


def test_resolve_cli_override(monkeypatch, tmp_path: Path) -> None:
    fake = tmp_path / "gog"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setenv("EZRA_GOG_CLI", str(fake))
    assert resolve_cli() == fake.resolve()


def test_config_gog_defaults() -> None:
    cfg = load_config()
    assert cfg.gog_enabled == "auto"
