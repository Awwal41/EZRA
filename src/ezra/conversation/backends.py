"""Chat backends for the conversation runtime.

Real local inference lives in :mod:`ezra.inference`. ``StubBackend`` is for
unit tests and ``ezra chat --backend stub`` dry-runs.
"""

from __future__ import annotations

from typing import Iterator, Protocol, runtime_checkable

from ezra.conversation.types import Message


@runtime_checkable
class ChatBackend(Protocol):
    """Minimal completion interface used by :class:`~ezra.conversation.Session`."""

    def complete(self, messages: list[Message], *, model: str) -> str:
        """Return a full assistant reply for ``messages``."""

    def stream(self, messages: list[Message], *, model: str) -> Iterator[str]:
        """Yield reply text in chunks (may be a single chunk)."""


class StubBackend:
    """Deterministic fake backend for tests and scaffolding.

    Replies with ``[stub:<model>] <last user message>``. Streaming yields the
    same text in fixed-size chunks.
    """

    def __init__(self, *, chunk_size: int = 24) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")
        self.chunk_size = chunk_size

    def complete(self, messages: list[Message], *, model: str) -> str:
        last_user = ""
        for msg in reversed(messages):
            if msg.role == "user":
                last_user = msg.content
                break
        return f"[stub:{model}] {last_user}"

    def stream(self, messages: list[Message], *, model: str) -> Iterator[str]:
        text = self.complete(messages, model=model)
        size = self.chunk_size
        for i in range(0, len(text), size):
            yield text[i : i + size]
