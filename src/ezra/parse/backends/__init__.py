"""Document parse backends (basic + MegaParse)."""

from __future__ import annotations

from ezra.parse.backends.basic import BasicParseBackend, basic_available
from ezra.parse.backends.megaparse import MegaParseBackend, megaparse_available

__all__ = [
    "BasicParseBackend",
    "MegaParseBackend",
    "basic_available",
    "megaparse_available",
]
