"""Conversation runtime: sessions, agent binding, pluggable chat backends.

Implements the design in ``docs/conversation.md``: session types, agent binding,
stub / llama / MLX backends, plus ``ezra chat`` and ``ezra serve``.
"""

from __future__ import annotations

from ezra.conversation.backends import ChatBackend, StubBackend
from ezra.conversation.session import (
    Session,
    open_session,
    resolve_session_model,
    sessions_dir,
)
from ezra.conversation.types import Message, Reply

__all__ = [
    "ChatBackend",
    "Message",
    "Reply",
    "Session",
    "StubBackend",
    "open_session",
    "resolve_session_model",
    "sessions_dir",
]
