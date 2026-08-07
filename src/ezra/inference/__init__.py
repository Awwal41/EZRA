"""Local inference backends (llama.cpp / MLX) for EZRA chat and serve."""

from __future__ import annotations

from ezra.inference.runtime import LocalRuntime, BackendUnavailable, create_backend
from ezra.inference.weights import WeightsError, find_gguf, resolve_model_dir

__all__ = [
    "BackendUnavailable",
    "LocalRuntime",
    "WeightsError",
    "create_backend",
    "find_gguf",
    "resolve_model_dir",
]
