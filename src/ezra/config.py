"""Configuration loading and path helpers for EZRA."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_NAME = "ezra.yaml"


def default_home() -> Path:
    """Return EZRA home directory (override with EZRA_HOME)."""
    env = os.environ.get("EZRA_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return Path.home() / ".ezra"


def default_models_dir() -> Path:
    """Return model cache directory (override with EZRA_MODELS_DIR)."""
    env = os.environ.get("EZRA_MODELS_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return default_home() / "models"


@dataclass
class EzraConfig:
    models_dir: Path = field(default_factory=default_models_dir)
    prefer_quant: str = "auto"
    hf_token_env: str = "HF_TOKEN"
    max_workers: int = 2
    resume: bool = True
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def hf_token(self) -> str | None:
        return os.environ.get(self.hf_token_env) or os.environ.get("HUGGING_FACE_HUB_TOKEN")


def _package_default_config() -> Path:
    return Path(__file__).resolve().parent / "defaults" / "ezra.yaml"


def load_config(path: Path | None = None) -> EzraConfig:
    """Load ezra.yaml from explicit path, cwd, EZRA_HOME, site profile, or packaged default."""
    candidates: list[Path] = []
    if path is not None:
        candidates.append(Path(path).expanduser())
    else:
        env_cfg = os.environ.get("EZRA_CONFIG")
        if env_cfg:
            candidates.append(Path(env_cfg).expanduser())
        # Per-cluster profile: export EZRA_SITE=my-cluster → sites/my-cluster/ezra.yaml
        site_name = os.environ.get("EZRA_SITE", "").strip()
        if site_name and "/" not in site_name and "\\" not in site_name:
            from ezra.hpc.sites import repo_root, sites_dir

            site_cfg = sites_dir(repo_root()) / site_name / "ezra.yaml"
            candidates.append(site_cfg)
        candidates.extend(
            [
                Path.cwd() / DEFAULT_CONFIG_NAME,
                default_home() / DEFAULT_CONFIG_NAME,
                _package_default_config(),
            ]
        )

    data: dict[str, Any] = {}
    for candidate in candidates:
        if candidate.is_file():
            with candidate.open(encoding="utf-8") as fh:
                loaded = yaml.safe_load(fh) or {}
            if not isinstance(loaded, dict):
                raise ValueError(f"Config must be a mapping: {candidate}")
            data = loaded
            break

    local = data.get("local") or {}
    models_dir = Path(
        local.get("models_dir")
        or os.environ.get("EZRA_MODELS_DIR")
        or default_models_dir()
    ).expanduser()

    return EzraConfig(
        models_dir=models_dir,
        prefer_quant=str(local.get("prefer_quant", "auto")),
        hf_token_env=str(local.get("hf_token_env", "HF_TOKEN")),
        max_workers=int(local.get("max_workers", 2)),
        resume=bool(local.get("resume", True)),
        raw=data,
    )
