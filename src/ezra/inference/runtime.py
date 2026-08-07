"""Local chat runtime: pick backend, cache loaded models, implement ChatBackend."""

from __future__ import annotations

import os
import platform
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Iterator, Literal

from ezra.config import EzraConfig
from ezra.conversation.backends import ChatBackend, StubBackend
from ezra.conversation.types import Message
from ezra.gallery import ModelGallery
from ezra.inference.llama_cpp_engine import LlamaCppEngine, llama_cpp_available
from ezra.inference.mlx_engine import MLXEngine, mlx_available
from ezra.inference.weights import (
    assert_chatable,
    find_gguf,
    find_mlx_model_dir,
    get_model_spec,
    recommended_backend,
    resolve_model_dir,
)

PreferName = Literal["auto", "llama", "mlx", "stub"]


class BackendUnavailable(RuntimeError):
    """Requested local backend cannot be created."""


@dataclass
class LocalRuntime:
    """Caches up to ``max_loaded`` engines and routes completions by gallery alias."""

    config: EzraConfig
    prefer: PreferName = "auto"
    gallery: ModelGallery = field(default_factory=ModelGallery)
    name: str = "local"
    _cache: OrderedDict[str, object] = field(default_factory=OrderedDict, repr=False)

    @property
    def backend_label(self) -> str:
        if self.prefer == "stub":
            return "stub"
        if self.prefer in ("llama", "mlx"):
            return self.prefer
        return "auto"

    def _max_loaded(self) -> int:
        return max(1, int(self.config.max_loaded))

    def _n_ctx(self) -> int:
        return int(self.config.n_ctx)

    def _n_gpu_layers(self) -> int:
        env = os.environ.get("EZRA_N_GPU_LAYERS", "").strip()
        if env:
            return int(env)
        return int(self.config.n_gpu_layers)

    def _pick_kind(self, model: str) -> PreferName:
        if self.prefer == "stub":
            return "stub"
        if self.prefer in ("llama", "mlx"):
            return self.prefer
        # auto
        spec = get_model_spec(model, self.gallery)
        kind = recommended_backend(spec)
        if kind == "mlx":
            if mlx_available() and platform.system() == "Darwin":
                return "mlx"
            if llama_cpp_available():
                # may still fail assert_chatable for non-gguf
                return "llama"
            return "mlx"
        if llama_cpp_available():
            return "llama"
        if mlx_available() and platform.system() == "Darwin":
            return "mlx"
        return "llama"

    def _load_engine(self, model: str) -> object:
        kind = self._pick_kind(model)
        if kind == "stub":
            return StubBackend()

        spec = get_model_spec(model, self.gallery)
        if kind == "llama":
            assert_chatable(spec, backend="llama")
            if not llama_cpp_available():
                raise BackendUnavailable(
                    "llama-cpp-python is not installed. "
                    "Install with: pip install -e '.[local]'"
                )
            model_dir = resolve_model_dir(model, self.config, self.gallery)
            gguf = find_gguf(model_dir, self.config.prefer_quant)
            return LlamaCppEngine(
                gguf,
                n_ctx=self._n_ctx(),
                n_gpu_layers=self._n_gpu_layers(),
            )

        assert_chatable(spec, backend="mlx")
        if not mlx_available():
            raise BackendUnavailable(
                "mlx-lm is not installed. "
                "Install with: pip install -e '.[mlx]'"
            )
        model_dir = resolve_model_dir(model, self.config, self.gallery)
        mlx_dir = find_mlx_model_dir(model_dir)
        return MLXEngine(mlx_dir)

    def get_engine(self, model: str) -> object:
        key = str(model).strip()
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        engine = self._load_engine(key)
        self._cache[key] = engine
        self._cache.move_to_end(key)
        while len(self._cache) > self._max_loaded():
            self._cache.popitem(last=False)
        return engine

    def complete(self, messages: list[Message], *, model: str) -> str:
        engine = self.get_engine(model)
        if isinstance(engine, StubBackend):
            return engine.complete(messages, model=model)
        return engine.complete(messages)  # type: ignore[no-any-return]

    def stream(self, messages: list[Message], *, model: str) -> Iterator[str]:
        engine = self.get_engine(model)
        if isinstance(engine, StubBackend):
            yield from engine.stream(messages, model=model)
            return
        yield from engine.stream(messages)  # type: ignore[misc]


def create_backend(
    config: EzraConfig,
    *,
    prefer: PreferName | str | None = None,
    gallery: ModelGallery | None = None,
) -> ChatBackend:
    """Build a :class:`LocalRuntime` (or stub) from config / preference.

    Raises:
        BackendUnavailable: required optional dependency missing for ``prefer``.
    """
    raw_prefer = prefer if prefer is not None else config.backend
    name = str(raw_prefer or "auto").strip().lower()
    if name not in ("auto", "llama", "mlx", "stub"):
        raise ValueError(
            f"Unknown backend {prefer!r}. Use auto, llama, mlx, or stub."
        )
    typed: PreferName = name  # type: ignore[assignment]

    if typed == "stub":
        return StubBackend()

    if typed == "llama" and not llama_cpp_available():
        raise BackendUnavailable(
            "llama-cpp-python is not installed. "
            "Install with: pip install -e '.[local]'"
        )
    if typed == "mlx" and not mlx_available():
        raise BackendUnavailable(
            "mlx-lm is not installed. "
            "Install with: pip install -e '.[mlx]'"
        )
    if typed == "auto" and not llama_cpp_available() and not mlx_available():
        raise BackendUnavailable(
            "No local inference backend installed. "
            "Try: pip install -e '.[local]'  (GGUF / llama.cpp) "
            "or on Apple Silicon: pip install -e '.[mlx]'"
        )

    return LocalRuntime(
        config=config,
        prefer=typed,
        gallery=gallery or ModelGallery(),
        name=typed,
    )
