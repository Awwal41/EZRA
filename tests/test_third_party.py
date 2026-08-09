"""Smoke tests: vendored third_party trees wire into EZRA adapters.

These checks do not run upstream CLIs, Gateways, or MegaParse OCR — they
assert that each in-tree snapshot is present and that adapter path helpers
resolve to it (integration wiring).
"""

from __future__ import annotations

import pytest

from ezra.gog import gog_root
from ezra.hpc.sites import repo_root
from ezra.openclaw import openclaw_root
from ezra.parse.backends.megaparse import _vendor_src
from ezra.peekaboo import peekaboo_root

_VENDORS: list[tuple[str, tuple[str, ...]]] = [
    ("OpenClaw", ("package.json", "UPSTREAM.txt", "LICENSE", "openclaw.mjs")),
    ("Peekaboo", ("README.md", "UPSTREAM.txt")),
    ("gogcli", ("go.mod", "UPSTREAM.txt", "README.md")),
    (
        "MegaParse",
        (
            "UPSTREAM.txt",
            "LICENSE",
            "src/megaparse/__init__.py",
            "src/megaparse_sdk/__init__.py",
        ),
    ),
]


@pytest.mark.parametrize("name,markers", _VENDORS)
def test_vendored_tree_present(name: str, markers: tuple[str, ...]) -> None:
    root = repo_root() / "third_party" / name
    assert root.is_dir(), f"missing third_party/{name} — restore the in-tree snapshot"
    for rel in markers:
        path = root / rel
        assert path.exists(), f"missing third_party/{name}/{rel}"


def test_adapter_roots_resolve_to_vendored_trees() -> None:
    oc = openclaw_root()
    assert oc is not None and oc.name == "OpenClaw"
    assert (oc / "UPSTREAM.txt").is_file()

    pk = peekaboo_root()
    assert pk is not None and pk.name == "Peekaboo"
    assert (pk / "UPSTREAM.txt").is_file()

    gg = gog_root()
    assert gg is not None and gg.name == "gogcli"
    assert (gg / "UPSTREAM.txt").is_file()

    mp_src = _vendor_src()
    assert mp_src.is_dir()
    assert mp_src.name == "src"
    assert mp_src.parent.name == "MegaParse"
    assert (mp_src / "megaparse").is_dir()
    assert (mp_src / "megaparse_sdk").is_dir()
