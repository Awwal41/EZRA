"""Tests for ezra.cline path helpers (no Node / Bun / agent required)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ezra.cli import main
from ezra.cline import cline_pin_info, cline_root, resolve_cli
from ezra.cline.local import PLACEHOLDER_API_KEY, local_provider_plan, serve_base_url
from ezra.config import load_config

needs_vendor = pytest.mark.skipif(
    cline_root() is None, reason="third_party/Cline not fetched — run scripts/fetch_third_party.py"
)


@needs_vendor
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


@needs_vendor
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


def test_resolve_cli_prefers_cmd_over_ps1(monkeypatch, tmp_path: Path) -> None:
    from ezra.cline.cli import resolve_cli as resolve_cli_impl

    ps1 = tmp_path / "cline.ps1"
    cmd = tmp_path / "cline.cmd"
    ps1.write_text("", encoding="utf-8")
    cmd.write_text("", encoding="utf-8")
    monkeypatch.delenv("EZRA_CLINE_CLI", raising=False)
    monkeypatch.setattr("ezra.cline.cli.shutil.which", lambda _name: str(ps1))
    assert resolve_cli_impl() == cmd.resolve()


def test_resolve_cli_npm_global_when_path_empty(monkeypatch, tmp_path: Path) -> None:
    from ezra.cline.cli import resolve_cli as resolve_cli_impl

    npm = tmp_path / "npm"
    npm.mkdir()
    shim = npm / "cline.cmd"
    shim.write_text("", encoding="utf-8")
    monkeypatch.delenv("EZRA_CLINE_CLI", raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr("ezra.cline.cli.shutil.which", lambda _name: None)
    monkeypatch.setattr("ezra.cline.cli.cline_root", lambda: None)
    assert resolve_cli_impl() == shim.resolve()


def test_config_cline_defaults() -> None:
    cfg = load_config()
    assert cfg.cline_enabled == "auto"


def test_local_provider_plan_needs_no_cloud_key() -> None:
    plan = local_provider_plan()
    assert plan["needs_cloud_key"] is False
    assert plan["provider"] == "openai-compatible"
    assert plan["api_key"] == PLACEHOLDER_API_KEY
    assert plan["base_url"] == serve_base_url()
    assert plan["base_url"].endswith("/v1")
    assert "-P" in plan["run_flags"]
    assert "openai-compatible" in plan["run_flags"]


def test_serve_base_url_rewrites_wildcard_bind() -> None:
    assert serve_base_url("0.0.0.0", 9000) == "http://127.0.0.1:9000/v1"


def test_cli_cline_use_local_json() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main, ["cline", "use-local", "--json", "--model", "qwen2.5-7b-instruct"]
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["needs_cloud_key"] is False
    assert payload["model"] == "qwen2.5-7b-instruct"
    assert payload["auth_argv"][0] == "auth"
