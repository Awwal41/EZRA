"""Sideload the EZRA Grid VSIX into Cursor / VS Code (never a marketplace)."""

from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path

from ezra.ide.pack import extension_version, package_vsix
from ezra.ide.paths import EXTENSION_ID, extension_folder_name, extension_root

_KIND_CURSOR = "cursor"
_KIND_CODE = "code"
_KIND_INSIDERS = "code-insiders"
_ALL_KINDS = (_KIND_CURSOR, _KIND_CODE, _KIND_INSIDERS)


class IdeNotFound(RuntimeError):
    """Raised when no VS Code / Cursor install (CLI or extensions dir) is found."""


@dataclass(frozen=True)
class IdeTarget:
    kind: str
    label: str
    cli: Path | None
    extensions_dir: Path


def _which(name: str) -> Path | None:
    found = shutil.which(name)
    return Path(found).resolve() if found else None


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.is_file():
            return path.resolve()
        # Windows shims are often .cmd next to a nameless entry
        cmd = path.with_suffix(".cmd")
        if cmd.is_file():
            return cmd.resolve()
        bat = path.with_suffix(".bat")
        if bat.is_file():
            return bat.resolve()
    return None


def _home() -> Path:
    return Path.home()


def _local_app_data() -> Path:
    env = os.environ.get("LOCALAPPDATA", "").strip()
    if env:
        return Path(env)
    return _home() / "AppData" / "Local"


def _cursor_cli_candidates() -> list[Path]:
    home = _home()
    local = _local_app_data()
    return [
        home / ".local" / "bin" / "cursor",
        Path("/usr/local/bin/cursor"),
        Path("/usr/bin/cursor"),
        Path("/Applications/Cursor.app/Contents/Resources/app/bin/cursor"),
        local / "Programs" / "cursor" / "resources" / "app" / "bin" / "cursor",
        local / "Programs" / "Cursor" / "resources" / "app" / "bin" / "cursor",
    ]


def _code_cli_candidates(*, insiders: bool) -> list[Path]:
    home = _home()
    local = _local_app_data()
    if insiders:
        return [
            home / ".local" / "bin" / "code-insiders",
            Path("/usr/local/bin/code-insiders"),
            Path("/usr/bin/code-insiders"),
            Path(
                "/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code"
            ),
            local
            / "Programs"
            / "Microsoft VS Code Insiders"
            / "bin"
            / "code-insiders",
        ]
    return [
        home / ".local" / "bin" / "code",
        Path("/usr/local/bin/code"),
        Path("/usr/bin/code"),
        Path("/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"),
        local / "Programs" / "Microsoft VS Code" / "bin" / "code",
    ]


def _extensions_dir(kind: str) -> Path:
    home = _home()
    if kind == _KIND_CURSOR:
        return home / ".cursor" / "extensions"
    if kind == _KIND_INSIDERS:
        return home / ".vscode-insiders" / "extensions"
    return home / ".vscode" / "extensions"


def _label(kind: str) -> str:
    return {
        _KIND_CURSOR: "Cursor",
        _KIND_CODE: "VS Code",
        _KIND_INSIDERS: "VS Code Insiders",
    }.get(kind, kind)


def discover_ides(kind: str = "auto") -> list[IdeTarget]:
    """Find Cursor / VS Code installs that can receive a sideloaded VSIX.

    A target counts if its CLI is on PATH (or a well-known location) **or**
    its extensions directory already exists (folder copy still works).
    """
    wanted: tuple[str, ...]
    if kind == "auto":
        wanted = _ALL_KINDS
    elif kind in _ALL_KINDS:
        wanted = (kind,)
    else:
        raise ValueError(f"Unknown IDE kind {kind!r}. Use auto, cursor, code, or code-insiders.")

    found: list[IdeTarget] = []
    for item in wanted:
        if item == _KIND_CURSOR:
            cli = _which("cursor") or _first_existing(_cursor_cli_candidates())
        elif item == _KIND_INSIDERS:
            cli = _which("code-insiders") or _first_existing(
                _code_cli_candidates(insiders=True)
            )
        else:
            cli = _which("code") or _first_existing(_code_cli_candidates(insiders=False))
        ext_dir = _extensions_dir(item)
        if item == _KIND_CURSOR:
            has_product = (
                (_local_app_data() / "Programs" / "cursor").is_dir()
                or (_local_app_data() / "Programs" / "Cursor").is_dir()
                or Path("/Applications/Cursor.app").is_dir()
            )
        elif item == _KIND_INSIDERS:
            has_product = (
                (_local_app_data() / "Programs" / "Microsoft VS Code Insiders").is_dir()
                or Path("/Applications/Visual Studio Code - Insiders.app").is_dir()
            )
        else:
            has_product = (
                (_local_app_data() / "Programs" / "Microsoft VS Code").is_dir()
                or Path("/Applications/Visual Studio Code.app").is_dir()
            )
        if cli is None and not ext_dir.is_dir() and not has_product:
            continue
        found.append(
            IdeTarget(
                kind=item,
                label=_label(item),
                cli=cli,
                extensions_dir=ext_dir,
            )
        )
    return found


def _run_cli_install(cli: Path, vsix: Path, *, force: bool) -> subprocess.CompletedProcess[str]:
    args = [str(cli), "--install-extension", str(vsix)]
    if force:
        args.append("--force")
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        timeout=120.0,
    )


def _extract_to_extensions_dir(vsix: Path, extensions_dir: Path, version: str) -> Path:
    dest = extensions_dir / extension_folder_name(version)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(vsix) as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if not name.startswith("extension/") or name.endswith("/"):
                continue
            rel = name[len("extension/") :]
            if not rel or ".." in Path(rel).parts:
                continue
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as out:
                shutil.copyfileobj(src, out)
    return dest


def install_vsix(
    vsix: Path | str | None = None,
    *,
    kind: str = "auto",
    force: bool = True,
    dry_run: bool = False,
    targets: list[IdeTarget] | None = None,
) -> list[dict[str, str | None]]:
    """Sideload the Grid VSIX. Never talks to a marketplace.

    Prefers ``cursor`` / ``code --install-extension``. If the CLI is missing,
    copies the payload into the editor's extensions folder (reload the window).
    """
    src = extension_root()
    version = extension_version(src)
    package = Path(vsix).expanduser().resolve() if vsix else package_vsix()
    if not package.is_file() and not dry_run:
        raise FileNotFoundError(f"VSIX not found: {package}. Run: ezra ide package")

    chosen = targets if targets is not None else discover_ides(kind)
    if not chosen:
        raise IdeNotFound(
            "No Cursor or VS Code install found. Install the editor, or pass "
            "--ide cursor|code after the CLI (`cursor` / `code`) is on PATH."
        )

    results: list[dict[str, str | None]] = []
    for target in chosen:
        record: dict[str, str | None] = {
            "kind": target.kind,
            "label": target.label,
            "cli": str(target.cli) if target.cli else None,
            "extensions_dir": str(target.extensions_dir),
            "vsix": str(package),
            "method": None,
            "destination": None,
            "status": "dry-run" if dry_run else None,
        }
        if dry_run:
            record["method"] = "cli" if target.cli else "folder"
            results.append(record)
            continue
        if target.cli is not None:
            proc = _run_cli_install(target.cli, package, force=force)
            record["method"] = "cli"
            record["status"] = "ok" if proc.returncode == 0 else "cli-failed"
            text = (proc.stdout or "") + (proc.stderr or "")
            record["output"] = text.strip() or None
            if proc.returncode == 0:
                results.append(record)
                continue
            # Fall through to folder copy if the CLI refused.
        dest = _extract_to_extensions_dir(package, target.extensions_dir, version)
        record["method"] = "folder"
        record["destination"] = str(dest)
        record["status"] = "ok"
        results.append(record)
    return results


def uninstall_extension(
    *,
    kind: str = "auto",
    dry_run: bool = False,
    targets: list[IdeTarget] | None = None,
) -> list[dict[str, str | None]]:
    """Remove a previous sideload (CLI uninstall and/or extensions folder)."""
    src = extension_root()
    version = extension_version(src)
    folder = extension_folder_name(version)
    chosen = targets if targets is not None else discover_ides(kind)
    if not chosen:
        raise IdeNotFound("No Cursor or VS Code install found to uninstall from.")

    results: list[dict[str, str | None]] = []
    for target in chosen:
        record: dict[str, str | None] = {
            "kind": target.kind,
            "label": target.label,
            "status": "dry-run" if dry_run else "absent",
        }
        dest = target.extensions_dir / folder
        if target.cli is not None and not dry_run:
            subprocess.run(
                [str(target.cli), "--uninstall-extension", EXTENSION_ID],
                check=False,
                capture_output=True,
                text=True,
                timeout=60.0,
            )
        if dest.is_dir():
            record["destination"] = str(dest)
            if not dry_run:
                shutil.rmtree(dest)
            record["status"] = "removed" if not dry_run else "dry-run"
        results.append(record)
    return results
