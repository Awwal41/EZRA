"""Core message / reply types for the conversation runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

Role = Literal["system", "user", "assistant"]


@dataclass
class Message:
    """One turn in a session (OpenAI-style roles)."""

    role: Role
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Message:
        role_raw = str(data.get("role") or "user")
        if role_raw not in ("system", "user", "assistant"):
            raise ValueError(f"Invalid message role: {role_raw!r}")
        role: Role = role_raw  # type: ignore[assignment]
        return cls(role=role, content=str(data.get("content") or ""))


@dataclass(frozen=True)
class Reply:
    """Result of :meth:`~ezra.conversation.Session.send`."""

    text: str
    model: str
    agent: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
