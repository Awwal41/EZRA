"""Document parsing engine with auto backend selection."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Protocol

from ezra.parse.backends.basic import BasicParseBackend
from ezra.parse.backends.megaparse import MegaParseBackend, megaparse_available
from ezra.parse.types import ParsedDocument

ParseBackendName = Literal["auto", "basic", "megaparse"]

# Office / rich formats that need MegaParse (or similar) rather than basic text.
_RICH_SUFFIXES = {
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
    ".xlsx",
    ".xls",
    ".odt",
    ".rtf",
    ".epub",
}


class ParseBackend(Protocol):
    name: str

    def parse(self, path: Path, *, strategy: str = "auto") -> ParsedDocument: ...


class DocumentParser:
    """EZRA-facing document parser.

    Prefer this over importing MegaParse directly so the rest of EZRA stays
    decoupled from upstream Quivr APIs.
    """

    def __init__(
        self,
        *,
        backend: ParseBackendName | str = "auto",
        strategy: str = "auto",
    ) -> None:
        self.backend_name = (backend or "auto").strip().lower()
        self.strategy = strategy or "auto"
        if self.backend_name not in {"auto", "basic", "megaparse"}:
            raise ValueError(
                f"Unknown parse backend {backend!r}. Use: auto | basic | megaparse"
            )

    def _pick(self, path: Path) -> ParseBackend:
        name = self.backend_name
        if name == "basic":
            return BasicParseBackend()
        if name == "megaparse":
            return MegaParseBackend()
        # auto
        suffix = path.suffix.lower()
        if suffix in _RICH_SUFFIXES and megaparse_available():
            return MegaParseBackend()
        if suffix in _RICH_SUFFIXES and not megaparse_available():
            # PDF can still work via pypdf; other office formats need MegaParse
            if suffix == ".pdf":
                return BasicParseBackend()
            raise RuntimeError(
                f"Parsing {suffix} requires MegaParse. "
                "Install with: pip install -e '.[parse]' (Python ≥ 3.11)."
            )
        return BasicParseBackend()

    def parse(self, path: Path | str) -> ParsedDocument:
        path = Path(path).expanduser().resolve()
        backend = self._pick(path)
        return backend.parse(path, strategy=self.strategy)


def parse_file(
    path: Path | str,
    *,
    backend: ParseBackendName | str = "auto",
    strategy: str = "auto",
) -> ParsedDocument:
    """Parse a document into LLM-ready text (convenience wrapper)."""
    return DocumentParser(backend=backend, strategy=strategy).parse(path)
