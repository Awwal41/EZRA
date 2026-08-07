"""llama.cpp backend via optional ``llama-cpp-python``."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from ezra.conversation.types import Message
from ezra.inference.weights import WeightsError


def llama_cpp_available() -> bool:
    try:
        import llama_cpp  # noqa: F401

        return True
    except ImportError:
        return False


def _require_llama() -> Any:
    try:
        from llama_cpp import Llama
    except ImportError as exc:
        raise WeightsError(
            "llama-cpp-python is not installed. "
            "Install local inference with: pip install -e '.[local]'"
        ) from exc
    return Llama


class LlamaCppEngine:
    """One loaded GGUF model."""

    def __init__(
        self,
        gguf_path: Path,
        *,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
        verbose: bool = False,
    ) -> None:
        Llama = _require_llama()
        self.path = Path(gguf_path)
        self._llm = Llama(
            model_path=str(self.path),
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            verbose=verbose,
        )

    def _openai_messages(self, messages: list[Message]) -> list[dict[str, str]]:
        return [m.to_dict() for m in messages]

    def complete(self, messages: list[Message], *, max_tokens: int = 1024) -> str:
        result = self._llm.create_chat_completion(
            messages=self._openai_messages(messages),
            max_tokens=max_tokens,
            stream=False,
        )
        choice = result["choices"][0]
        message = choice.get("message") or {}
        return str(message.get("content") or "")

    def stream(self, messages: list[Message], *, max_tokens: int = 1024) -> Iterator[str]:
        stream = self._llm.create_chat_completion(
            messages=self._openai_messages(messages),
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            content = delta.get("content")
            if content:
                yield str(content)
