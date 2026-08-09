"""Tests for ezra.openclaw path helpers (no Node / Gateway required)."""

from __future__ import annotations

from pathlib import Path

from ezra.config import load_config
from ezra.openclaw import openclaw_pin_info, openclaw_root, resolve_cli


def test_openclaw_root_points_at_submodule() -> None:
    root = openclaw_root()
    assert root is not None
    assert root.name == "OpenClaw"
    assert (root / "package.json").is_file()
    assert (root / "LICENSE").is_file()
    assert (root / "openclaw.mjs").is_file()


def test_pin_info_has_version() -> None:
    info = openclaw_pin_info()
    assert info["upstream"].endswith("/openclaw")
    assert info["license"] == "MIT"
    assert "version" in info


def test_resolve_cli_override(monkeypatch, tmp_path: Path) -> None:
    fake = tmp_path / "openclaw"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setenv("EZRA_OPENCLAW_CLI", str(fake))
    assert resolve_cli() == fake.resolve()


def test_config_openclaw_defaults() -> None:
    cfg = load_config()
    assert cfg.openclaw_enabled == "auto"
