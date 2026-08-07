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
    """Return default model cache directory (``~/.ezra/models``).

    Prefer :func:`resolve_models_dir` when applying CLI / env / yaml overrides.
    """
    return default_home() / "models"


def resolve_models_dir(
    *,
    cli_override: Path | str | None = None,
    yaml_value: Path | str | None = None,
) -> Path:
    """Resolve where model weights are stored.

    Precedence (highest first):

    1. ``cli_override`` (``--models-dir``)
    2. ``EZRA_MODELS_DIR`` environment variable
    3. ``yaml_value`` (``local.models_dir`` in ezra.yaml)
    4. ``~/.ezra/models`` (or ``$EZRA_HOME/models``)
    """
    if cli_override is not None and str(cli_override).strip():
        return Path(cli_override).expanduser().resolve()
    env = os.environ.get("EZRA_MODELS_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    if yaml_value is not None and str(yaml_value).strip():
        return Path(yaml_value).expanduser().resolve()
    return default_models_dir().resolve()


@dataclass
class EzraConfig:
    models_dir: Path = field(default_factory=default_models_dir)
    prefer_quant: str = "auto"
    hf_token_env: str = "HF_TOKEN"
    max_workers: int = 2
    resume: bool = True
    backend: str = "auto"
    max_loaded: int = 2
    n_ctx: int = 4096
    n_gpu_layers: int = -1
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
    models_dir = resolve_models_dir(yaml_value=local.get("models_dir"))

    n_gpu = local.get("n_gpu_layers", -1)
    env_layers = os.environ.get("EZRA_N_GPU_LAYERS", "").strip()
    if env_layers:
        n_gpu = int(env_layers)

    return EzraConfig(
        models_dir=models_dir,
        prefer_quant=str(local.get("prefer_quant", "auto")),
        hf_token_env=str(local.get("hf_token_env", "HF_TOKEN")),
        max_workers=int(local.get("max_workers", 2)),
        resume=bool(local.get("resume", True)),
        backend=str(local.get("backend", "auto")),
        max_loaded=int(local.get("max_loaded", 2)),
        n_ctx=int(local.get("n_ctx", 4096)),
        n_gpu_layers=int(n_gpu),
        raw=data,
    )
