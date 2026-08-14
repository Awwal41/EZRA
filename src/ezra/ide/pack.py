"""Build a VSIX from ``ide/vscode`` with the stdlib zipper (no vsce / npm)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from ezra.ide.paths import EXTENSION_NAME, PUBLISHER, extension_root

_SKIP_DIR_NAMES = {
    ".git",
    ".vscode",
    "node_modules",
    "dist",
    "__pycache__",
}
_SKIP_SUFFIXES = {".vsix", ".pyc", ".pyo"}
_SKIP_FILE_NAMES = {".ds_store", "thumbs.db"}

_CONTENT_TYPES = {
    ".css": "text/css",
    ".html": "text/html",
    ".js": "application/javascript",
    ".json": "application/json",
    ".md": "text/markdown",
    ".svg": "image/svg+xml",
    ".txt": "text/plain",
    ".vsixmanifest": "text/xml",
    ".xml": "text/xml",
    ".png": "image/png",
    ".woff": "font/woff",
}


class ExtensionSourceMissing(FileNotFoundError):
    """Raised when ``ide/vscode`` is not in this checkout."""


def _read_manifest(src: Path) -> dict:
    data = json.loads((src / "package.json").read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid package.json: {src / 'package.json'}")
    return data


def extension_version(src: Path | None = None) -> str:
    root = src if src is not None else extension_root()
    if root is None:
        raise ExtensionSourceMissing(
            "IDE extension sources missing. Restore ide/vscode from the EZRA repo."
        )
    return str(_read_manifest(root).get("version") or "0.0.0")


def _vsixmanifest(pkg: dict) -> str:
    ident = str(pkg.get("name") or EXTENSION_NAME)
    version = str(pkg.get("version") or "0.0.0")
    publisher = str(pkg.get("publisher") or PUBLISHER)
    display = escape(str(pkg.get("displayName") or "EZRA Grid"))
    description = escape(str(pkg.get("description") or "EZRA Grid"))
    engines = pkg.get("engines") if isinstance(pkg.get("engines"), dict) else {}
    engine = escape(str(engines.get("vscode") or "^1.85.0"))
    return f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="{escape(ident)}" Version="{escape(version)}" Publisher="{escape(publisher)}" />
    <DisplayName>{display}</DisplayName>
    <Description xml:space="preserve">{description}</Description>
    <Tags>ezra,ai,local,offline,cline,openclaw</Tags>
    <Categories>Other</Categories>
    <GalleryFlags>Private Preview</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{engine}" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionDependencies" Value="" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionPack" Value="" />
      <Property Id="Microsoft.VisualStudio.Services.Links.Source" Value="https://github.com/Awwal41/EZRA" />
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code"/>
  </Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true" />
  </Assets>
</PackageManifest>
"""


def _content_types(extensions: set[str]) -> str:
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '  <Default Extension="vsixmanifest" ContentType="text/xml"/>',
        '  <Default Extension="xml" ContentType="text/xml"/>',
    ]
    seen = {"vsixmanifest", "xml"}
    for ext in sorted(extensions):
        key = ext.lstrip(".").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        ctype = _CONTENT_TYPES.get(f".{key}", "application/octet-stream")
        lines.append(f'  <Default Extension="{key}" ContentType="{ctype}"/>')
    lines.append("</Types>")
    lines.append("")
    return "\n".join(lines)


def _iter_extension_files(src: Path) -> list[Path]:
    files: list[Path] = []
    for path in src.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(src).parts
        if any(part in _SKIP_DIR_NAMES for part in rel_parts):
            continue
        if path.name.lower() in _SKIP_FILE_NAMES:
            continue
        if path.suffix.lower() in _SKIP_SUFFIXES:
            continue
        files.append(path)
    return files


def default_vsix_path(src: Path | None = None) -> Path:
    root = src if src is not None else extension_root()
    if root is None:
        raise ExtensionSourceMissing(
            "IDE extension sources missing. Restore ide/vscode from the EZRA repo."
        )
    version = extension_version(root)
    return (root / "dist" / f"{EXTENSION_NAME}-{version}.vsix").resolve()


def package_vsix(
    dest: Path | str | None = None,
    *,
    src: Path | None = None,
) -> Path:
    """Zip ``ide/vscode`` into a VSIX. Does not talk to any marketplace.

    ``dest`` defaults to ``ide/vscode/dist/ezra-grid-<version>.vsix``.
    """
    root = src if src is not None else extension_root()
    if root is None:
        raise ExtensionSourceMissing(
            "IDE extension sources missing. Restore ide/vscode from the EZRA repo."
        )
    pkg = _read_manifest(root)
    out = Path(dest).expanduser().resolve() if dest else default_vsix_path(root)
    out.parent.mkdir(parents=True, exist_ok=True)

    files = _iter_extension_files(root)
    suffixes = {p.suffix.lower() for p in files if p.suffix}
    manifest = _vsixmanifest(pkg)
    types_xml = _content_types(suffixes)

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("extension.vsixmanifest", manifest)
        zf.writestr("[Content_Types].xml", types_xml)
        for path in files:
            arc = "extension/" + path.relative_to(root).as_posix()
            zf.write(path, arcname=arc)
    return out
