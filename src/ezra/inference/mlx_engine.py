"""Apple MLX backend via optional ``mlx-lm``."""

from __future__ import annotations

import platform
from pathlib import Path
from typing import Any, Iterator

from ezra.conversation.types import Message
from ezra.inference.weights import WeightsError


def mlx_available() -> bool:
    try:
        import mlx_lm  # noqa: F401

        return True
    except ImportError:
        return False


def _require_mlx() -> tuple[Any, Any, Any]:
    if platform.system() != "Darwin":
        raise WeightsError(
            "MLX backend is only supported on macOS (Apple Silicon). "
            "Use --backend llama with a GGUF model: pip install -e '.[local]'"
        )
    try:
        from mlx_lm import generate, load, stream_generate
    except ImportError as exc:
        raise WeightsError(
            "mlx-lm is not installed. "
            "Install Apple Silicon inference with: pip install -e '.[mlx]'"
        ) from exc
    return load, generate, stream_generate


def _format_chat(messages: list[Message], tokenizer: Any) -> str:
    openai_msgs = [m.to_dict() for m in messages]
    apply = getattr(tokenizer, "apply_chat_template", None)
    if callable(apply):
        try:
            return apply(openai_msgs, tokenize=False, add_generation_prompt=True)
        except Exception:
            pass
    parts: list[str] = []
    for msg in messages:
        parts.append(f"{msg.role.upper()}: {msg.content}")
    parts.append("ASSISTANT:")
    return "\n".join(parts)


class MLXEngine:
    """One loaded MLX / HF-layout model directory."""

    def __init__(self, model_dir: Path, *, max_tokens: int = 1024) -> None:
        load, generate, stream_generate = _require_mlx()
        self.path = Path(model_dir)
        self._default_max_tokens = max_tokens
        self._model, self._tokenizer = load(str(self.path))
        self._generate = generate
        self._stream_generate = stream_generate

    def complete(self, messages: list[Message], *, max_tokens: int | None = None) -> str:
        prompt = _format_chat(messages, self._tokenizer)
        limit = max_tokens if max_tokens is not None else self._default_max_tokens
        text = self._generate(
            self._model,
            self._tokenizer,
            prompt=prompt,
            max_tokens=limit,
            verbose=False,
        )
        return str(text)

    def stream(self, messages: list[Message], *, max_tokens: int | None = None) -> Iterator[str]:
        prompt = _format_chat(messages, self._tokenizer)
        limit = max_tokens if max_tokens is not None else self._default_max_tokens
        for item in self._stream_generate(
            self._model,
            self._tokenizer,
            prompt=prompt,
            max_tokens=limit,
        ):
            # mlx_lm may yield strings or objects with .text
            if isinstance(item, str):
                if item:
                    yield item
            else:
                text = getattr(item, "text", None)
                if text:
                    yield str(text)
