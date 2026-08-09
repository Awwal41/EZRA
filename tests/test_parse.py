"""Tests for ezra.parse (basic backend; MegaParse optional)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ezra.parse import DocumentParser, ParsedDocument, parse_file
from ezra.parse.backends.basic import BasicParseBackend


def test_parse_markdown(tmp_path: Path) -> None:
    f = tmp_path / "notes.md"
    f.write_text("# Title\n\nHello EZRA.\n", encoding="utf-8")
    doc = parse_file(f, backend="basic")
    assert isinstance(doc, ParsedDocument)
    assert doc.backend == "basic"
    assert "Hello EZRA" in doc.text
    assert doc.path == f.resolve()


def test_as_chat_context_truncates(tmp_path: Path) -> None:
    f = tmp_path / "long.txt"
    f.write_text("abcdef", encoding="utf-8")
    doc = parse_file(f, backend="basic")
    ctx = doc.as_chat_context(max_chars=3)
    assert "truncated" in ctx
    assert "abc" in ctx
    assert "def" not in ctx.split("\n\n", 1)[-1]


def test_basic_reads_unknown_suffix_as_text(tmp_path: Path) -> None:
    f = tmp_path / "notes.tmp"
    f.write_text("lab note", encoding="utf-8")
    doc = BasicParseBackend().parse(f)
    assert "lab note" in doc.text


def test_auto_office_without_megaparse(tmp_path: Path) -> None:
    f = tmp_path / "deck.pptx"
    f.write_bytes(b"PK\x03\x04not-a-real-pptx")
    with pytest.raises(RuntimeError, match="MegaParse"):
        DocumentParser(backend="auto").parse(f)


def test_document_parser_auto_text(tmp_path: Path) -> None:
    f = tmp_path / "mol.smi"
    f.write_text("CCO\n", encoding="utf-8")
    doc = DocumentParser(backend="auto").parse(f)
    assert doc.backend == "basic"
    assert doc.text.strip() == "CCO"


def test_parse_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_file(tmp_path / "nope.txt", backend="basic")


def test_config_parse_defaults() -> None:
    from ezra.config import load_config

    cfg = load_config()
    assert cfg.parse_backend == "auto"
    assert cfg.parse_strategy == "auto"
