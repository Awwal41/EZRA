"""Tests for inference weight helpers and backend factory."""

from __future__ import annotations

from pathlib import Path

import pytest

from ezra.config import EzraConfig
from ezra.gallery import ModelSpec
from ezra.inference.runtime import BackendUnavailable, LocalRuntime, create_backend
from ezra.inference.weights import (
    WeightsError,
    assert_chatable,
    find_gguf,
    find_mlx_model_dir,
    recommended_backend,
)


def test_find_gguf_prefers_quant(tmp_path: Path) -> None:
    d = tmp_path / "m"
    d.mkdir()
    (d / "model-Q4_K_M.gguf").write_bytes(b"a" * 10)
    (d / "model-Q8_0.gguf").write_bytes(b"b" * 100)
    assert find_gguf(d, "Q4_K_M").name == "model-Q4_K_M.gguf"
    assert find_gguf(d, "auto").name == "model-Q8_0.gguf"


def test_find_gguf_missing(tmp_path: Path) -> None:
    with pytest.raises(WeightsError, match="No .gguf"):
        find_gguf(tmp_path)


def test_find_mlx_model_dir(tmp_path: Path) -> None:
    nested = tmp_path / "snap" / "subdir"
    nested.mkdir(parents=True)
    (nested / "config.json").write_text("{}", encoding="utf-8")
    assert find_mlx_model_dir(tmp_path) == nested


def test_assert_chatable() -> None:
    gguf = ModelSpec(name="a", repo_id="x/y", format="gguf")
    st = ModelSpec(name="b", repo_id="x/y", format="safetensors")
    assert_chatable(gguf, backend="llama")
    with pytest.raises(WeightsError):
        assert_chatable(st, backend="llama")
    assert_chatable(st, backend="mlx")
    with pytest.raises(WeightsError):
        assert_chatable(gguf, backend="mlx")
    assert recommended_backend(gguf) == "llama"
    assert recommended_backend(st) == "mlx"


def test_create_backend_stub() -> None:
    from ezra.conversation import StubBackend

    cfg = EzraConfig()
    backend = create_backend(cfg, prefer="stub")
    assert isinstance(backend, StubBackend)


def test_create_backend_missing_llama(monkeypatch: pytest.MonkeyPatch) -> None:
    import ezra.inference.runtime as runtime_mod

    monkeypatch.setattr(runtime_mod, "llama_cpp_available", lambda: False)
    monkeypatch.setattr(runtime_mod, "mlx_available", lambda: False)
    with pytest.raises(BackendUnavailable, match=r"\.\[local\]"):
        create_backend(EzraConfig(), prefer="auto")
    with pytest.raises(BackendUnavailable, match="llama-cpp"):
        create_backend(EzraConfig(), prefer="llama")


def test_local_runtime_with_fake_llama(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Load path uses mocked LlamaCppEngine without native wheels."""
    import ezra.inference.runtime as runtime_mod

    model_dir = tmp_path / "models" / "phi-3.5-mini-instruct"
    model_dir.mkdir(parents=True)
    (model_dir / "phi.Q4_K_M.gguf").write_bytes(b"gguf")

    class FakeEngine:
        def complete(self, messages, *, max_tokens: int = 1024):
            return "fake-reply"

        def stream(self, messages, *, max_tokens: int = 1024):
            yield "fake"
            yield "-stream"

    monkeypatch.setattr(runtime_mod, "llama_cpp_available", lambda: True)
    monkeypatch.setattr(
        runtime_mod,
        "LlamaCppEngine",
        lambda *a, **k: FakeEngine(),
    )
    monkeypatch.setattr(
        runtime_mod,
        "resolve_model_dir",
        lambda name, config, gallery=None: model_dir,
    )
    monkeypatch.setattr(
        runtime_mod,
        "get_model_spec",
        lambda name, gallery=None: ModelSpec(
            name=name, repo_id="x/y", format="gguf"
        ),
    )

    cfg = EzraConfig(models_dir=tmp_path / "models", max_loaded=1)
    runtime = LocalRuntime(config=cfg, prefer="llama")
    from ezra.conversation.types import Message

    msgs = [Message(role="user", content="hi")]
    assert runtime.complete(msgs, model="phi-3.5-mini-instruct") == "fake-reply"
    assert "".join(runtime.stream(msgs, model="phi-3.5-mini-instruct")) == "fake-stream"
    # cache hit
    assert "phi-3.5-mini-instruct" in runtime._cache
