"""Unit tests for gallery + download selection (no network)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ezra.downloader import ModelDownloader
from ezra.gallery import ModelGallery, load_gallery
from ezra.config import EzraConfig


def test_gallery_loads_and_has_unique_names() -> None:
    gallery = load_gallery()
    names = gallery.names()
    assert len(names) >= 5
    assert len(names) == len(set(names))
    assert gallery.get("qwen2.5-7b-instruct").repo_id


def test_gallery_get_prefix() -> None:
    gallery = load_gallery()
    # unique substring
    spec = gallery.get("chemllm")
    assert spec.name == "chemllm-7b"


def test_gallery_filter_science() -> None:
    gallery = load_gallery()
    science = gallery.list(science_only=True)
    assert science
    assert all(s.science_tags for s in science)


def test_gallery_filter_tag() -> None:
    gallery = load_gallery()
    chem = gallery.list(tag="chemistry")
    assert chem
    assert all("chemistry" in s.all_tags for s in chem)


def test_download_dry_run_all(tmp_path: Path) -> None:
    config = EzraConfig(models_dir=tmp_path / "models")
    dl = ModelDownloader(config, ModelGallery())
    results = dl.download_many(
        all_models=True,
        include_gated=False,
        max_size_b=4,
        dry_run=True,
        workers=1,
    )
    assert results
    assert all(r.status == "skipped" for r in results)


def test_download_unknown_model(tmp_path: Path) -> None:
    config = EzraConfig(models_dir=tmp_path / "models")
    dl = ModelDownloader(config, ModelGallery())
    result = dl.download_one("definitely-not-a-real-model-xyz")
    assert result.status == "failed"
