"""Shared types for EZRA document parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ParsedDocument:
    """Normalized parse result for LLM / RAG / chat context."""

    path: Path
    text: str
    backend: str
    strategy: str = "auto"
    file_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_chat_context(self, *, max_chars: int | None = None) -> str:
        """Format document text for injection into a chat / agent prompt."""
        body = self.text if max_chars is None else self.text[:max_chars]
        name = self.path.name
        header = f"[Document: {name}]"
        if max_chars is not None and len(self.text) > max_chars:
            header += f" (truncated to {max_chars} chars)"
        return f"{header}\n\n{body}"
