"""Lightweight local parser for plain text and simple PDFs (no MegaParse)."""

from __future__ import annotations

from pathlib import Path

from ezra.parse.types import ParsedDocument

_TEXT_SUFFIXES = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".csv",
    ".tsv",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".toml",
    ".py",
    ".r",
    ".jl",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".ts",
    ".sh",
    ".bat",
    ".ps1",
    ".html",
    ".htm",
    ".xml",
    ".tex",
    ".bib",
    ".cif",
    ".xyz",
    ".smi",
    ".smiles",
}


def basic_available() -> bool:
    return True


def _read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF parsing with the basic backend needs pypdf. "
            "Install with: pip install -e '.[parse-basic]' "
            "or use MegaParse: pip install -e '.[parse]'"
        ) from exc
    reader = PdfReader(str(path))
    parts: list[str] = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            parts.append(f"<!-- page {i + 1} -->\n{text.strip()}")
    return "\n\n".join(parts).strip()


class BasicParseBackend:
    """Parse plain-text science artifacts and simple digital PDFs."""

    name = "basic"

    def parse(self, path: Path, *, strategy: str = "auto") -> ParsedDocument:
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            text = _read_pdf(path)
            file_type = "pdf"
        elif suffix in _TEXT_SUFFIXES or suffix == "":
            text = _read_text(path)
            file_type = suffix.lstrip(".") or "text"
        else:
            # Best-effort: many lab artifacts are text without a known suffix.
            try:
                text = _read_text(path)
                file_type = suffix.lstrip(".") or "text"
            except OSError as exc:
                raise ValueError(
                    f"Basic backend cannot parse {suffix!r}. "
                    "Install MegaParse extras: pip install -e '.[parse]' "
                    f"(or convert {path.name} to text/PDF)."
                ) from exc

        return ParsedDocument(
            path=path,
            text=text,
            backend=self.name,
            strategy=strategy,
            file_type=file_type,
            metadata={"bytes": path.stat().st_size},
        )
