"""Locate installed model weights for local inference."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from ezra.config import EzraConfig
from ezra.downloader import ModelDownloader
from ezra.gallery import ModelGallery, ModelSpec

BackendKind = Literal["llama", "mlx"]


class WeightsError(RuntimeError):
    """Missing or unsuitable weights for chat."""


def resolve_model_dir(
    name: str,
    config: EzraConfig,
    gallery: ModelGallery | None = None,
) -> Path:
    """Return the install directory for a gallery alias."""
    downloader = ModelDownloader(config, gallery or ModelGallery())
    path = downloader.local_path(name)
    if path is None:
        raise WeightsError(
            f"Model {name!r} is not installed under {config.models_dir}. "
            f"Download it with: ezra models download {name}"
        )
    return path


def get_model_spec(name: str, gallery: ModelGallery | None = None) -> ModelSpec:
    gal = gallery or ModelGallery()
    try:
        return gal.get(name)
    except KeyError as exc:
        raise WeightsError(
            f"Unknown gallery model {name!r}. Try: ezra models list"
        ) from exc


def find_gguf(model_dir: Path, prefer_quant: str = "auto") -> Path:
    """Pick a ``.gguf`` file under ``model_dir``.

    Prefer filenames containing ``prefer_quant`` (when not ``auto``), else the
    largest GGUF (heuristic for higher-quality quants often being bigger).
    """
    root = Path(model_dir)
    files = sorted(root.rglob("*.gguf"))
    files = [p for p in files if p.is_file()]
    if not files:
        raise WeightsError(
            f"No .gguf weights found under {root}. "
            "Download a GGUF gallery model for llama.cpp chat."
        )
    quant = (prefer_quant or "auto").strip()
    if quant.lower() != "auto":
        matched = [p for p in files if quant.lower() in p.name.lower()]
        if matched:
            files = matched
    files.sort(key=lambda p: p.stat().st_size, reverse=True)
    return files[0]


def find_mlx_model_dir(model_dir: Path) -> Path:
    """Return a directory mlx-lm can load (has ``config.json``)."""
    root = Path(model_dir)
    if (root / "config.json").is_file():
        return root
    for child in sorted(root.rglob("config.json")):
        return child.parent
    raise WeightsError(
        f"No MLX / Hugging Face model layout (config.json) under {root}. "
        "Install mlx-lm weights or use a GGUF model with the llama backend."
    )


def recommended_backend(spec: ModelSpec) -> BackendKind:
    """Suggest backend from gallery format."""
    fmt = (spec.format or "").lower()
    if fmt == "gguf":
        return "llama"
    return "mlx"


def assert_chatable(
    spec: ModelSpec,
    *,
    backend: BackendKind,
) -> None:
    """Raise :class:`WeightsError` if ``spec`` cannot run on ``backend``."""
    fmt = (spec.format or "").lower()
    if backend == "llama":
        if fmt and fmt != "gguf":
            raise WeightsError(
                f"Model {spec.name!r} is format={spec.format!r}; llama.cpp needs GGUF. "
                f"Download a GGUF gallery model (ezra models list --format gguf) "
                f"or use --backend mlx on Apple Silicon (pip install -e '.[mlx]')."
            )
        return
    if backend == "mlx":
        if fmt == "gguf":
            raise WeightsError(
                f"Model {spec.name!r} is GGUF; use --backend llama "
                "(pip install -e '.[local]') instead of mlx."
            )
        return
