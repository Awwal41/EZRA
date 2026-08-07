"""Conversation runtime: sessions, agent binding, pluggable chat backends.

Phase 1 of the design in ``docs/conversation.md``: session types + stub backend.
Wire ``ezra chat`` / ``ezra serve`` once local inference lands.
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
