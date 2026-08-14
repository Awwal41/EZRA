"""Tests for ezra.ide (sideload Grid; no editor or marketplace required)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from click.testing import CliRunner

from ezra.cli import main
from ezra.config import load_config
from ezra.ide import (
    EXTENSION_ID,
    IdeTarget,
    extension_root,
    install_vsix,
    package_vsix,
    probe_grid,
)
from ezra.ide.pack import extension_version
from ezra.ide.paths import PUBLISHER, extension_folder_name


def test_extension_root_points_at_in_tree_sources() -> None:
    root = extension_root()
    assert root is not None
    assert root.name == "vscode"
    assert root.parent.name == "ide"
    assert (root / "package.json").is_file()
    assert (root / "src" / "extension.js").is_file()
    assert (root / "media" / "grid.js").is_file()
    assert (root / "media" / "icon.svg").is_file()
    pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
    assert pkg["publisher"] == PUBLISHER
    assert pkg["name"] == "ezra-grid"
    assert pkg.get("private") is True


def test_package_vsix_is_offline_zip(tmp_path: Path) -> None:
    dest = tmp_path / "ezra-grid.vsix"
    out = package_vsix(dest)
    assert out == dest.resolve()
    assert dest.is_file()
    with zipfile.ZipFile(dest) as zf:
        names = set(zf.namelist())
    assert "extension.vsixmanifest" in names
    assert "[Content_Types].xml" in names
    assert "extension/package.json" in names
    assert "extension/src/extension.js" in names
    assert "extension/media/grid.css" in names
    assert "extension/README.md" in names
    manifest = zipfile.ZipFile(dest).read("extension.vsixmanifest").decode("utf-8")
    assert PUBLISHER in manifest
    assert "ezra-grid" in manifest
    types_xml = zipfile.ZipFile(dest).read("[Content_Types].xml").decode("utf-8")
    assert "javascript" in types_xml


def test_probe_grid_has_lanes_and_never_marketplace() -> None:
    payload = probe_grid()
    assert payload["marketplace"] is False
    assert payload["auto_install"] is False
    assert payload["auto_start"] is False
    assert payload["extension_id"] == EXTENSION_ID
    assert set(payload["lanes"]) == {"local", "agent", "cline", "openclaw"}
    assert payload["lanes"]["cline"]["needs_cloud_key"] is False
    assert payload["lanes"]["cline"]["provider"] == "openai-compatible"
    assert "chem-assistant" in [a["name"] for a in payload["lanes"]["agent"]["agents"]]


def test_install_dry_run_uses_injected_targets(tmp_path: Path) -> None:
    vsix = package_vsix(tmp_path / "g.vsix")
    fake = IdeTarget(
        kind="cursor",
        label="Cursor",
        cli=None,
        extensions_dir=tmp_path / "ext",
    )
    rows = install_vsix(vsix, dry_run=True, targets=[fake])
    assert len(rows) == 1
    assert rows[0]["status"] == "dry-run"
    assert rows[0]["method"] == "folder"
    assert not (tmp_path / "ext").exists()


def test_install_folder_copy(tmp_path: Path) -> None:
    vsix = package_vsix(tmp_path / "g.vsix")
    ext_dir = tmp_path / "extensions"
    fake = IdeTarget(
        kind="code",
        label="VS Code",
        cli=None,
        extensions_dir=ext_dir,
    )
    rows = install_vsix(vsix, force=True, targets=[fake])
    assert rows[0]["status"] == "ok"
    assert rows[0]["method"] == "folder"
    dest = ext_dir / extension_folder_name(extension_version())
    assert (dest / "package.json").is_file()
    assert (dest / "src" / "extension.js").is_file()


def test_config_ide_defaults() -> None:
    cfg = load_config()
    assert cfg.ide_enabled == "auto"


def test_cli_ide_status_probe_package(tmp_path: Path) -> None:
    runner = CliRunner()
    status = runner.invoke(main, ["ide", "status", "--json"])
    assert status.exit_code == 0, status.output
    payload = json.loads(status.output)
    assert payload["marketplace"] is False
    assert payload["auto_install"] is False
    probe = runner.invoke(main, ["ide", "probe", "--json"])
    assert probe.exit_code == 0, probe.output
    data = json.loads(probe.output)
    assert "lanes" in data
    dest = tmp_path / "grid.vsix"
    packed = runner.invoke(main, ["ide", "package", "-o", str(dest)])
    assert packed.exit_code == 0, packed.output
    assert dest.is_file()
    help_out = runner.invoke(main, ["ide", "--help"])
    assert help_out.exit_code == 0
    assert "install" in help_out.output
    assert "package" in help_out.output
