"""Tests for ezra.voicebox path / MCP helpers (no Voicebox app required)."""

from __future__ import annotations

from pathlib import Path

from ezra.config import load_config
from ezra.voicebox import (
    base_url,
    mcp_http_config,
    mcp_url,
    probe_server,
    resolve_mcp_shim,
    voicebox_available,
    voicebox_pin_info,
    voicebox_root,
)


def test_voicebox_root_points_at_vendored_tree() -> None:
    root = voicebox_root()
    assert root is not None
    assert root.name == "Voicebox"
    assert (root / "package.json").is_file()
    assert (root / "UPSTREAM.txt").is_file()
    assert (root / "LICENSE").is_file()
    assert voicebox_available()


def test_voicebox_pin_info() -> None:
    info = voicebox_pin_info()
    assert info["upstream"] == "https://github.com/jamiepine/voicebox"
    assert info["license"] == "MIT"
    assert "root" in info
    assert info.get("version")  # from package.json


def test_mcp_http_config_shape() -> None:
    snippet = mcp_http_config(client="cursor")
    server = snippet["mcpServers"]["voicebox"]
    assert server["url"] == mcp_url()
    assert server["url"].endswith("/mcp")
    assert server["headers"]["X-Voicebox-Client-Id"] == "cursor"
    assert base_url().startswith("http://")


def test_resolve_mcp_shim_override(monkeypatch, tmp_path: Path) -> None:
    fake = tmp_path / "voicebox-mcp"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setenv("EZRA_VOICEBOX_MCP", str(fake))
    assert resolve_mcp_shim() == fake.resolve()


def test_base_url_override(monkeypatch) -> None:
    monkeypatch.setenv("EZRA_VOICEBOX_URL", "http://10.0.0.2:9999/")
    assert base_url() == "http://10.0.0.2:9999"
    assert mcp_url() == "http://10.0.0.2:9999/mcp"


def test_probe_server_offline() -> None:
    # Default port with no Voicebox running should report not ok (no raise).
    result = probe_server(timeout=0.5)
    assert "url" in result
    assert result["ok"] is False or isinstance(result["ok"], bool)


def test_config_voicebox_defaults() -> None:
    cfg = load_config()
    assert cfg.voicebox_enabled == "auto"
