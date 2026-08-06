"""Tests for ezra init-config."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from ezra.cli import main


def test_init_config_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path
    (root / "ezra.yaml.example").write_text(
        "version: 1\nlocal:\n  models_dir: ~/.ezra/models\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text("[project]\nname='ezra'\n", encoding="utf-8")
    (root / ".env.example").write_text("# EZRA_SITE=demo\n", encoding="utf-8")
    monkeypatch.setenv("EZRA_ROOT", str(root))
    monkeypatch.chdir(root)

    runner = CliRunner()
    result = runner.invoke(main, ["init-config", "--cwd", "--env"])
    assert result.exit_code == 0, result.output
    assert (root / "ezra.yaml").is_file()
    assert (root / ".env").is_file()

    again = runner.invoke(main, ["init-config", "--cwd"])
    assert again.exit_code != 0
