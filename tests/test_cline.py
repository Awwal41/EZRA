"""Tests for ezra.cline path helpers (no Node / Bun / agent required)."""

from __future__ import annotations

from pathlib import Path

from ezra.cline import cline_pin_info, cline_root, resolve_cli
from ezra.config import load_config


def test_cline_root_points_at_vendored_tree() -> None:
    root = cline_root()
    assert root is not None
    assert root.name == "Cline"
    assert (root / "package.json").is_file()
    assert (root / "LICENSE").is_file()
    assert (root / "UPSTREAM.txt").is_file()
    assert (root / "apps" / "cli" / "package.json").is_file()
    assert (root / "apps" / "cli" / "src" / "index.ts").is_file()
    assert (root / "sdk" / "packages" / "sdk" / "package.json").is_file()
    assert (root / "evals" / "cline-bench" / "README.md").is_file()


def test_pin_info_has_version() -> None:
    info = cline_pin_info()
    assert info["upstream"].endswith("/cline")
    assert info["license"] == "Apache-2.0"
    assert "version" in info


def test_resolve_cli_override(monkeypatch, tmp_path: Path) -> None:
    fake = tmp_path / "cline"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setenv("EZRA_CLINE_CLI", str(fake))
    assert resolve_cli() == fake.resolve()


def test_config_cline_defaults() -> None:
    cfg = load_config()
    assert cfg.cline_enabled == "auto"
