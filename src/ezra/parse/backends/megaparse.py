"""Adapter around Quivr MegaParse (vendored under third_party/MegaParse)."""

from __future__ import annotations

import sys
from pathlib import Path

from ezra.parse.types import ParsedDocument


def _vendor_src() -> Path:
    """Return ``third_party/MegaParse/src`` when running from the EZRA repo."""
    # .../src/ezra/parse/backends/megaparse.py → repo root
    here = Path(__file__).resolve()
    repo_root = here.parents[4]
    return repo_root / "third_party" / "MegaParse" / "src"


def _ensure_import_path() -> None:
    vendor = _vendor_src()
    if vendor.is_dir():
        vendor_s = str(vendor)
        if vendor_s not in sys.path:
            sys.path.insert(0, vendor_s)


def megaparse_available() -> bool:
    """True if MegaParse (and its hard runtime deps) can be imported."""
    try:
        _ensure_import_path()
        import megaparse  # noqa: F401
        from megaparse import MegaParse  # noqa: F401

        return True
    except Exception:
        return False


def _map_strategy(strategy: str):
    from megaparse_sdk.schema.parser_config import StrategyEnum

    key = (strategy or "auto").strip().lower().replace("-", "_")
    mapping = {
        "auto": StrategyEnum.AUTO,
        "fast": StrategyEnum.FAST,
        "hi_res": StrategyEnum.HI_RES,
        "hires": StrategyEnum.HI_RES,
        "high_res": StrategyEnum.HI_RES,
    }
    if key not in mapping:
        raise ValueError(
            f"Unknown MegaParse strategy {strategy!r}. "
            "Use: auto | fast | hi_res"
        )
    return mapping[key]


class MegaParseBackend:
    """LLM-oriented document parser via vendored / installed MegaParse."""

    name = "megaparse"

    def __init__(self) -> None:
        _ensure_import_path()
        try:
            from megaparse import MegaParse
        except ImportError as exc:
            raise RuntimeError(
                "MegaParse is not available. From the EZRA repo root run:\n"
                "  pip install -e '.[parse]'\n"
                "Requires Python ≥ 3.11, plus system deps (poppler, tesseract). "
                "See third_party/MegaParse/README.md and "
                "https://github.com/QuivrHQ/MegaParse"
            ) from exc
        self._cls = MegaParse

    def parse(self, path: Path, *, strategy: str = "auto") -> ParsedDocument:
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        strat = _map_strategy(strategy)
        parser = self._cls()
        text = parser.load(file_path=path, strategy=strat)
        return ParsedDocument(
            path=path,
            text=str(text),
            backend=self.name,
            strategy=strategy or "auto",
            file_type=path.suffix.lstrip(".").lower(),
            metadata={"bytes": path.stat().st_size},
        )
