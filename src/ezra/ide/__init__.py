"""Sideload-only IDE extension helpers (VS Code / Cursor).

The Grid lives under ``ide/vscode/`` in the EZRA checkout. EZRA packages a
``.vsix`` locally and installs it with the editor CLI (or by copying into the
extensions folder). Nothing is published to a marketplace.

Safety defaults:

- Never auto-installs into an IDE
- Never auto-starts Cline or OpenClaw
- The extension only invokes those CLIs when you pick that lane and send

Typical usage::

    from ezra.ide import extension_root, package_vsix, probe_grid

    src = extension_root()
    vsix = package_vsix()
    print(probe_grid()["lanes"].keys())
"""

from __future__ import annotations

from ezra.ide.install import (
    IdeNotFound,
    IdeTarget,
    discover_ides,
    install_vsix,
    uninstall_extension,
)
from ezra.ide.pack import package_vsix
from ezra.ide.paths import EXTENSION_ID, PUBLISHER, extension_root
from ezra.ide.probe import probe_grid

__all__ = [
    "EXTENSION_ID",
    "PUBLISHER",
    "IdeNotFound",
    "IdeTarget",
    "discover_ides",
    "extension_root",
    "install_vsix",
    "package_vsix",
    "probe_grid",
    "uninstall_extension",
]
