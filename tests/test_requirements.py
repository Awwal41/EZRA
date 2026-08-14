"""Requirements files that keep llama.cpp on a pre-built wheel."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

IDE_FILES = (
    "requirements-ide-cpu.txt",
    "requirements-ide-cuda124.txt",
    "requirements-ide-cuda121.txt",
    "requirements-ide-macos.txt",
)

WHEEL_INDEX = {
    "requirements-ide-cpu.txt": "https://abetlen.github.io/llama-cpp-python/whl/cpu",
    "requirements-ide-cuda124.txt": "https://abetlen.github.io/llama-cpp-python/whl/cu124",
    "requirements-ide-cuda121.txt": "https://abetlen.github.io/llama-cpp-python/whl/cu121",
    "requirements-ide-macos.txt": "https://abetlen.github.io/llama-cpp-python/whl/metal",
}


def test_core_and_serve_requirement_files_exist() -> None:
    for name in ("requirements.txt", "requirements-serve.txt"):
        path = ROOT / name
        assert path.is_file(), f"missing {name}"
        text = path.read_text(encoding="utf-8")
        assert "click" in text or "fastapi" in text


def test_ide_requirement_files_force_wheels() -> None:
    for name in IDE_FILES:
        path = ROOT / name
        assert path.is_file(), f"missing {name}"
        text = path.read_text(encoding="utf-8")
        assert "-e ." in text
        assert "llama-cpp-python" in text
        assert "--only-binary=llama-cpp-python" in text
        assert "--extra-index-url" in text
        assert WHEEL_INDEX[name] in text


def test_getting_started_and_wheel_cheat_sheet_exist() -> None:
    gs = ROOT / "docs" / "getting-started.md"
    cheat = ROOT / "requirements" / "README.md"
    assert gs.is_file()
    assert cheat.is_file()
    body = gs.read_text(encoding="utf-8")
    assert "requirements-ide-cpu.txt" in body
    assert "EZRA: Open Grid" in body
    assert "wheel" in body.lower()
