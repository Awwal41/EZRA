"""Tests for per-cluster site profiles."""

from __future__ import annotations

from pathlib import Path

import pytest

from ezra.config import load_config
from ezra.hpc.sbatch import generate_script
from ezra.hpc.sites import init_site, list_sites, validate_site_name


def test_validate_site_name() -> None:
    assert validate_site_name("frontier") == "frontier"
    with pytest.raises(ValueError):
        validate_site_name("_template")
    with pytest.raises(ValueError):
        validate_site_name("../evil")


def test_init_site_copies_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Point repo root at a fake tree with the real template copied in
    sites = tmp_path / "sites"
    template = sites / "_template"
    template.mkdir(parents=True)
    (template / "ezra.yaml").write_text("version: 1\nhpc: {enabled: true}\n", encoding="utf-8")
    (template / "modules.sh").write_text("# modules\n", encoding="utf-8")
    (template / "NOTES.md").write_text("# notes\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='ezra'\n", encoding="utf-8")

    monkeypatch.setenv("EZRA_ROOT", str(tmp_path))
    profile = init_site("demo-cluster", root=tmp_path)
    assert profile.path.is_dir()
    assert profile.config_path.is_file()
    assert profile.modules_path.is_file()
    assert list_sites(tmp_path)[0].name == "demo-cluster"

    with pytest.raises(FileExistsError):
        init_site("demo-cluster", root=tmp_path)

    init_site("demo-cluster", root=tmp_path, force=True)


def test_load_config_respects_ezra_site(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='ezra'\n", encoding="utf-8")
    site = tmp_path / "sites" / "lab"
    site.mkdir(parents=True)
    (site / "ezra.yaml").write_text(
        "version: 1\nlocal:\n  prefer_quant: Q8_0\n  max_workers: 1\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("EZRA_ROOT", str(tmp_path))
    monkeypatch.setenv("EZRA_SITE", "lab")
    monkeypatch.delenv("EZRA_CONFIG", raising=False)
    monkeypatch.chdir(tmp_path)

    cfg = load_config()
    assert cfg.prefer_quant == "Q8_0"
    assert cfg.max_workers == 1


def test_init_site_models_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sites = tmp_path / "sites"
    template = sites / "_template"
    template.mkdir(parents=True)
    (template / "ezra.yaml").write_text(
        "version: 1\nlocal:\n  models_dir: ~/.ezra/models\n",
        encoding="utf-8",
    )
    (template / "modules.sh").write_text("# modules\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='ezra'\n", encoding="utf-8")
    monkeypatch.setenv("EZRA_ROOT", str(tmp_path))

    profile = init_site("lab", root=tmp_path, models_dir="/scratch/u/ezra/models")
    text = profile.config_path.read_text(encoding="utf-8")
    assert "models_dir: /scratch/u/ezra/models" in text


def test_generated_script_embeds_models_dir() -> None:
    script = generate_script("download", models_dir="/scratch/u/ezra/models")
    assert "/scratch/u/ezra/models" in script
    assert "EZRA_MODELS_DIR=" in script


def test_generated_script_mentions_site_profile() -> None:
    script = generate_script("download")
    assert "EZRA_SITE" in script
    assert "ezra hpc init-site" in script
