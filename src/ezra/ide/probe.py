"""JSON snapshot of Grid lanes for the IDE extension (no agent auto-start)."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any

from ezra import __version__
from ezra.ide.install import discover_ides
from ezra.ide.pack import extension_version
from ezra.ide.paths import EXTENSION_ID, extension_root


_CLINE_SHIMS = {"cline", "cline.cmd", "cline.exe", "cline.ps1", "cline.bat"}


def _windows_cline_argv(cli: Path | None = None) -> list[str]:
    """``cline.cmd`` path so PowerShell does not load the blocked ``cline.ps1``."""
    candidates: list[Path] = []
    if cli is not None:
        if cli.suffix.lower() == ".cmd":
            candidates.append(cli)
        candidates.append(cli.with_name("cline.cmd"))
    appdata = os.environ.get("APPDATA", "").strip()
    if appdata:
        candidates.append(Path(appdata) / "npm" / "cline.cmd")
    for path in candidates:
        if path.is_file():
            return [str(path)]
    return ["cline.cmd"]


def _cli_argv(cli: Path | None, *, fallback: str | None = None) -> list[str] | None:
    """Argv the Grid terminal can run (node/bun prefix for JS/TS entries).

    On Windows, npm shims become the ``.cmd`` path so PowerShell does not try
    to load ``cline.ps1`` (blocked when script execution is disabled). A
    vendored ``.ts``/``.js`` entry without Bun/Node uses ``fallback``.
    """
    if cli is None:
        return None
    name = cli.name.lower()
    if name in _CLINE_SHIMS:
        if os.name == "nt":
            return _windows_cline_argv(cli)
        return ["cline"]
    suffix = cli.suffix.lower()
    if suffix == ".ts":
        bun = shutil.which("bun")
        if bun:
            return [bun, str(cli)]
        if fallback:
            return _windows_cline_argv() if os.name == "nt" else [fallback]
        return None
    if suffix in {".js", ".mjs", ".cjs"}:
        node = shutil.which("node")
        if node:
            return [node, str(cli)]
        if fallback:
            return _windows_cline_argv() if os.name == "nt" else [fallback]
        return None
    return [str(cli)]


def probe_grid(*, config: Any = None) -> dict[str, Any]:
    """Describe EZRA / Cline / OpenClaw lanes for the Grid webview.

    Read-only: does not start serve, Cline, or the OpenClaw Gateway.
    """
    from ezra.agents import list_agents
    from ezra.cline import cline_available, cline_root, resolve_cli as resolve_cline
    from ezra.cline.local import local_provider_plan
    from ezra.config import load_config
    from ezra.downloader import ModelDownloader
    from ezra.gallery import ModelGallery
    from ezra.openclaw import (
        openclaw_available,
        openclaw_root,
        resolve_cli as resolve_openclaw,
    )

    cfg = config if config is not None else load_config()
    gallery = ModelGallery()
    dl = ModelDownloader(cfg, gallery)
    installed = [s.name for s in dl.list_installed()]
    agents = [{"name": p.name, "path": str(p.path)} for p in list_agents()]
    src = extension_root()
    cline_cli = resolve_cline()
    openclaw_cli = resolve_openclaw()
    cline_plan = local_provider_plan(config=cfg)
    ides = []
    for target in discover_ides("auto"):
        ides.append(
            {
                "kind": target.kind,
                "label": target.label,
                "cli": str(target.cli) if target.cli else None,
                "extensions_dir": str(target.extensions_dir),
            }
        )
    return {
        "ezra_version": __version__,
        "extension_id": EXTENSION_ID,
        "extension_version": extension_version(src) if src else None,
        "extension_root": str(src) if src else None,
        "marketplace": False,
        "auto_install": False,
        "auto_start": False,
        "python": sys.executable,
        "ides": ides,
        "lanes": {
            "local": {
                "id": "local",
                "label": "EZRA local",
                "ready": bool(installed),
                "models_installed": installed,
                "gallery_size": len(gallery.names()),
                "backend": cfg.backend,
                "note": "Gallery GGUF on this machine via ezra chat (off grid).",
            },
            "agent": {
                "id": "agent",
                "label": "Personal agent",
                "ready": bool(agents),
                "agents": agents,
                "note": "Binds agents/<name>/ prompt + preferred models.",
            },
            "cline": {
                "id": "cline",
                "label": "Cline",
                "ready": cline_cli is not None
                and _cli_argv(cline_cli, fallback="cline") is not None,
                "available": cline_available(),
                "root": str(cline_root()) if cline_root() else None,
                "cli": str(cline_cli) if cline_cli else None,
                "argv": _cli_argv(cline_cli, fallback="cline"),
                "enabled": cfg.cline_enabled,
                "needs_cloud_key": False,
                "provider": cline_plan["provider"],
                "base_url": cline_plan["base_url"],
                "model": cline_plan["model"],
                "run_flags": cline_plan["run_flags"],
                "auth_argv": cline_plan["auth_argv"],
                "serve_argv": cline_plan["serve_argv"],
                "hint": cline_plan.get("hint"),
                "note": cline_plan["note"],
            },
            "openclaw": {
                "id": "openclaw",
                "label": "OpenClaw",
                "ready": openclaw_cli is not None
                and _cli_argv(openclaw_cli) is not None,
                "available": openclaw_available(),
                "root": str(openclaw_root()) if openclaw_root() else None,
                "cli": str(openclaw_cli) if openclaw_cli else None,
                "argv": _cli_argv(openclaw_cli),
                "enabled": cfg.openclaw_enabled,
                "note": "Gateway / personal agent. EZRA never auto-starts it.",
            },
        },
    }
