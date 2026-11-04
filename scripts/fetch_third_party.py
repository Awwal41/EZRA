#!/usr/bin/env python3
"""Download EZRA's third-party integrations into ``third_party/`` at pinned versions.

The public EZRA repository does not ship these source trees. Each one is fetched
from its upstream GitHub repository at the exact commit EZRA was built against,
so the ``ezra.*`` adapters (OpenClaw, Peekaboo, gogcli, MegaParse, Cline,
Voicebox) resolve the same layout as a vendored checkout.

Usage::

    python scripts/fetch_third_party.py              # all vendors
    python scripts/fetch_third_party.py Cline Voicebox
    python scripts/fetch_third_party.py --force      # re-download existing trees
    python scripts/fetch_third_party.py --list

Requires ``git`` on PATH. Each upstream keeps its own license (MIT or Apache-2.0).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
THIRD_PARTY = REPO_ROOT / "third_party"


@dataclass(frozen=True)
class Vendor:
    name: str
    url: str
    commit: str
    license: str
    label: str = ""
    submodules: bool = False


VENDORS: tuple[Vendor, ...] = (
    Vendor(
        "OpenClaw",
        "https://github.com/openclaw/openclaw",
        "v2026.6.34",
        "MIT",
        label="tag v2026.6.34",
    ),
    Vendor(
        "Peekaboo",
        "https://github.com/openclaw/Peekaboo",
        "ae58d77640384c5c6973550c31bddf30c6b3c57a",
        "MIT",
        submodules=True,
    ),
    Vendor(
        "gogcli",
        "https://github.com/openclaw/gogcli",
        "402def5041d68dc65df04f8b082f2a2fd7750fb5",
        "MIT",
        label="tag v0.35.0",
    ),
    Vendor(
        "MegaParse",
        "https://github.com/QuivrHQ/MegaParse",
        "ba9a24aec950d6cf14834b8e2e11f5725778f12e",
        "Apache-2.0",
    ),
    Vendor(
        "Cline",
        "https://github.com/cline/cline",
        "afab68f3a3c28e7c288a76f0907631972d9122b2",
        "Apache-2.0",
        submodules=True,
    ),
    Vendor(
        "Voicebox",
        "https://github.com/jamiepine/voicebox",
        "51f49dea198384b4eb6087b72c17057c6eb1c1cd",
        "MIT",
    ),
)


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", "-c", "core.longpaths=true", *args], cwd=cwd, check=True)


def _checkout(vendor: Vendor, dest: Path) -> None:
    dest.mkdir(parents=True)
    _git("init", "--quiet", cwd=dest)
    _git("remote", "add", "origin", vendor.url, cwd=dest)
    _git("fetch", "--quiet", "--depth", "1", "origin", vendor.commit, cwd=dest)
    _git("checkout", "--quiet", "FETCH_HEAD", cwd=dest)
    if vendor.submodules:
        _git("submodule", "update", "--quiet", "--init", "--recursive", "--depth", "1", cwd=dest)


def _megaparse_layout(dest: Path) -> None:
    """Expose ``src/megaparse`` and ``src/megaparse_sdk`` as ``ezra.parse`` expects."""
    src = dest / "src"
    src.mkdir(exist_ok=True)
    for pkg, origin in (
        ("megaparse", dest / "libs" / "megaparse" / "src" / "megaparse"),
        ("megaparse_sdk", dest / "libs" / "megaparse_sdk" / "megaparse_sdk"),
    ):
        if not origin.is_dir():
            raise RuntimeError(f"MegaParse upstream layout changed: missing {origin}")
        shutil.copytree(origin, src / pkg, dirs_exist_ok=True)


def _write_upstream(vendor: Vendor, dest: Path) -> None:
    pin = vendor.commit + (f" ({vendor.label})" if vendor.label else "")
    (dest / "UPSTREAM.txt").write_text(
        f"Source: {vendor.url}\n"
        f"License: {vendor.license} (see LICENSE in this directory)\n"
        f"Pinned ref: {pin}\n"
        f"Fetched by scripts/fetch_third_party.py on {datetime.now(timezone.utc).date().isoformat()}\n",
        encoding="utf-8",
    )


def _rmtree(path: Path) -> None:
    def _make_writable(func, p, _exc):  # git pack files are read-only on Windows
        Path(p).chmod(0o700)
        func(p)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_make_writable)
    else:
        shutil.rmtree(path, onerror=_make_writable)


def fetch(vendor: Vendor, *, force: bool) -> None:
    dest = THIRD_PARTY / vendor.name
    if (dest / "UPSTREAM.txt").is_file() and not force:
        print(f"[skip] {vendor.name}: already present (use --force to re-download)")
        return
    if dest.exists():
        _rmtree(dest)
    print(f"[fetch] {vendor.name} <- {vendor.url} @ {vendor.label or vendor.commit[:12]}")
    try:
        _checkout(vendor, dest)
        if vendor.name == "MegaParse":
            _megaparse_layout(dest)
        _write_upstream(vendor, dest)
    except BaseException:
        if dest.exists():
            _rmtree(dest)
        raise
    print(f"[ok]    {vendor.name} -> {dest.relative_to(REPO_ROOT)}")


def main(argv: list[str] | None = None) -> int:
    names = [v.name for v in VENDORS]
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("vendors", nargs="*", metavar="NAME", help=f"subset of: {', '.join(names)}")
    parser.add_argument("--force", action="store_true", help="re-download trees that already exist")
    parser.add_argument("--list", action="store_true", help="print pinned vendors and exit")
    args = parser.parse_args(argv)

    if args.list:
        for v in VENDORS:
            print(f"{v.name:10} {v.license:11} {v.url} @ {v.label or v.commit}")
        return 0

    lookup = {v.name.lower(): v for v in VENDORS}
    unknown = [n for n in args.vendors if n.lower() not in lookup]
    if unknown:
        parser.error(f"unknown vendor(s): {', '.join(unknown)}; choose from {', '.join(names)}")
    selected = [lookup[n.lower()] for n in args.vendors] or list(VENDORS)

    if shutil.which("git") is None:
        print("error: git is required on PATH", file=sys.stderr)
        return 1

    failed: list[str] = []
    for vendor in selected:
        try:
            fetch(vendor, force=args.force)
        except (subprocess.CalledProcessError, RuntimeError, OSError) as exc:
            print(f"[fail]  {vendor.name}: {exc}", file=sys.stderr)
            failed.append(vendor.name)
    if failed:
        print(f"\nFailed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
