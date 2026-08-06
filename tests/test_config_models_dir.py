"""Tests for model storage path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from ezra.config import load_config, resolve_models_dir


def test_resolve_cli_beats_env_and_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EZRA_MODELS_DIR", str(tmp_path / "from-env"))
    got = resolve_models_dir(
        cli_override=tmp_path / "from-cli",
        yaml_value=str(tmp_path / "from-yaml"),
    )
    assert got == (tmp_path / "from-cli").resolve()


def test_resolve_env_beats_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EZRA_MODELS_DIR", str(tmp_path / "from-env"))
    got = resolve_models_dir(yaml_value=str(tmp_path / "from-yaml"))
    assert got == (tmp_path / "from-env").resolve()


def test_resolve_yaml_when_no_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EZRA_MODELS_DIR", raising=False)
    got = resolve_models_dir(yaml_value=str(tmp_path / "from-yaml"))
    assert got == (tmp_path / "from-yaml").resolve()


def test_load_config_env_overrides_yaml_models_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg_path = tmp_path / "ezra.yaml"
    cfg_path.write_text(
        "version: 1\nlocal:\n  models_dir: ~/.ezra/models\n  prefer_quant: auto\n",
        encoding="utf-8",
    )
    env_dir = tmp_path / "scratch-models"
    monkeypatch.setenv("EZRA_MODELS_DIR", str(env_dir))
    monkeypatch.delenv("EZRA_CONFIG", raising=False)
    monkeypatch.delenv("EZRA_SITE", raising=False)

    cfg = load_config(cfg_path)
    assert cfg.models_dir == env_dir.resolve()
