"""Document parsing for LLM ingestion (MegaParse + lightweight basic backend).

Typical usage::

    from ezra.parse import parse_file

    doc = parse_file("paper.pdf")
    session.send(doc.as_chat_context() + "\\n\\nSummarize the methods.")

Install MegaParse runtime deps with ``pip install -e ".[parse]"`` (Python ≥ 3.11).
Vendored sources live under ``third_party/MegaParse/`` (Apache-2.0).
"""

from __future__ import annotations

from ezra.parse.backends.basic import basic_available
from ezra.parse.backends.megaparse import megaparse_available
from ezra.parse.engine import DocumentParser, parse_file
from ezra.parse.types import ParsedDocument

__all__ = [
    "DocumentParser",
    "ParsedDocument",
    "basic_available",
    "megaparse_available",
    "parse_file",
]
