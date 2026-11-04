"""Smoke tests: third_party trees wire into EZRA adapters.

These checks do not run upstream CLIs, Gateways, or MegaParse OCR — they
assert that each downloaded tree is present and that adapter path helpers
resolve to it (integration wiring). Run ``python scripts/fetch_third_party.py``
first; tests for vendors that have not been fetched are skipped.
"""

from __future__ import annotations

import pytest

from ezra.cline import cline_root
from ezra.gog import gog_root
from ezra.hpc.sites import repo_root
from ezra.openclaw import openclaw_root
from ezra.parse.backends.megaparse import _vendor_src
from ezra.peekaboo import peekaboo_root
from ezra.voicebox import voicebox_root

_VENDORS: list[tuple[str, tuple[str, ...]]] = [
    ("OpenClaw", ("package.json", "UPSTREAM.txt", "LICENSE", "openclaw.mjs")),
    ("Peekaboo", ("README.md", "UPSTREAM.txt")),
    ("gogcli", ("go.mod", "UPSTREAM.txt", "README.md")),
    (
        "Cline",
        (
            "package.json",
            "UPSTREAM.txt",
            "LICENSE",
            "apps/cli/src/index.ts",
            "evals/cline-bench/README.md",
        ),
    ),
    (
        "MegaParse",
        (
            "UPSTREAM.txt",
            "LICENSE",
            "src/megaparse/__init__.py",
            "src/megaparse_sdk/__init__.py",
        ),
    ),
    (
        "Voicebox",
        (
            "package.json",
            "UPSTREAM.txt",
            "LICENSE",
            "backend/main.py",
        ),
    ),
]


def _fetched(name: str) -> bool:
    return (repo_root() / "third_party" / name / "UPSTREAM.txt").is_file()


@pytest.mark.parametrize("name,markers", _VENDORS)
def test_vendored_tree_present(name: str, markers: tuple[str, ...]) -> None:
    if not _fetched(name):
        pytest.skip(f"third_party/{name} not fetched — run scripts/fetch_third_party.py")
    root = repo_root() / "third_party" / name
    for rel in markers:
        path = root / rel
        assert path.exists(), f"missing third_party/{name}/{rel}"


def test_adapter_roots_resolve_to_vendored_trees() -> None:
    missing = [name for name, _ in _VENDORS if not _fetched(name)]
    if missing:
        pytest.skip(f"third_party not fetched: {', '.join(missing)}")

    oc = openclaw_root()
    assert oc is not None and oc.name == "OpenClaw"
    assert (oc / "UPSTREAM.txt").is_file()

    pk = peekaboo_root()
    assert pk is not None and pk.name == "Peekaboo"
    assert (pk / "UPSTREAM.txt").is_file()

    gg = gog_root()
    assert gg is not None and gg.name == "gogcli"
    assert (gg / "UPSTREAM.txt").is_file()

    cl = cline_root()
    assert cl is not None and cl.name == "Cline"
    assert (cl / "UPSTREAM.txt").is_file()

    vb = voicebox_root()
    assert vb is not None and vb.name == "Voicebox"
    assert (vb / "UPSTREAM.txt").is_file()

    mp_src = _vendor_src()
    assert mp_src.is_dir()
    assert mp_src.name == "src"
    assert mp_src.parent.name == "MegaParse"
    assert (mp_src / "megaparse").is_dir()
    assert (mp_src / "megaparse_sdk").is_dir()
