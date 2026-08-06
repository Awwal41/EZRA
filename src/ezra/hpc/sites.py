"""Resolve per-cluster site profiles under ``sites/<name>/``."""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

_SITE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,62}$")


@dataclass(frozen=True)
class SiteProfile:
    name: str
    path: Path

    @property
    def config_path(self) -> Path:
        return self.path / "ezra.yaml"

    @property
    def modules_path(self) -> Path:
        return self.path / "modules.sh"

    @property
    def notes_path(self) -> Path:
        return self.path / "NOTES.md"


def repo_root() -> Path:
    """Return the EZRA checkout root (parent of ``sites/`` / ``pyproject.toml``)."""
    env = os.environ.get("EZRA_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    # src/ezra/hpc/sites.py → parents: hpc, ezra, src, repo
    here = Path(__file__).resolve()
    candidate = here.parents[3]
    if (candidate / "pyproject.toml").is_file():
        return candidate
    return Path.cwd()


def sites_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "sites"


def template_dir(root: Path | None = None) -> Path:
    return sites_dir(root) / "_template"


def validate_site_name(name: str) -> str:
    name = name.strip()
    if name.startswith("_"):
        raise ValueError("Site name must not start with '_' (reserved for templates).")
    if name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError(f"Invalid site name: {name!r}")
    if not _SITE_NAME_RE.match(name):
        raise ValueError(
            f"Invalid site name {name!r}. Use letters, numbers, dots, dashes, underscores."
        )
    return name


def list_sites(root: Path | None = None) -> list[SiteProfile]:
    base = sites_dir(root)
    if not base.is_dir():
        return []
    profiles: list[SiteProfile] = []
    for child in sorted(base.iterdir()):
        if not child.is_dir() or child.name.startswith("_") or child.name.startswith("."):
            continue
        profiles.append(SiteProfile(name=child.name, path=child))
    return profiles


def get_site(name: str, root: Path | None = None) -> SiteProfile:
    name = validate_site_name(name)
    path = sites_dir(root) / name
    if not path.is_dir():
        raise FileNotFoundError(
            f"Site profile not found: {path}. "
            f"Create one with: ezra hpc init-site {name}"
        )
    return SiteProfile(name=name, path=path)


def current_site(root: Path | None = None) -> SiteProfile | None:
    """Return the profile named by ``EZRA_SITE``, if set."""
    name = os.environ.get("EZRA_SITE", "").strip()
    if not name:
        return None
    return get_site(name, root)


def patch_models_dir(config_path: Path, models_dir: str | Path) -> None:
    """Set ``local.models_dir`` in an ezra.yaml while preserving comments when possible."""
    path = Path(config_path)
    value = str(Path(models_dir).as_posix() if isinstance(models_dir, Path) else models_dir)
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"^([ \t]*models_dir:[ \t]*).*$", re.MULTILINE)
    if pattern.search(text):
        updated = pattern.sub(rf"\g<1>{value}", text, count=1)
    else:
        # No models_dir key yet - append under local: if present, else create a stub
        local_match = re.search(r"^local:\s*$", text, re.MULTILINE)
        if local_match:
            insert_at = local_match.end()
            updated = text[:insert_at] + f"\n  models_dir: {value}" + text[insert_at:]
        else:
            updated = text.rstrip() + f"\n\nlocal:\n  models_dir: {value}\n"
    path.write_text(updated, encoding="utf-8", newline="\n")


def init_site(
    name: str,
    root: Path | None = None,
    *,
    force: bool = False,
    models_dir: str | Path | None = None,
) -> SiteProfile:
    """Copy ``sites/_template`` to ``sites/<name>``."""
    name = validate_site_name(name)
    root = root or repo_root()
    src = template_dir(root)
    if not src.is_dir():
        raise FileNotFoundError(f"Missing template directory: {src}")
    dest = sites_dir(root) / name
    if dest.exists():
        if not force:
            raise FileExistsError(
                f"Site already exists: {dest}. Use --force to overwrite, or pick another name."
            )
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    profile = SiteProfile(name=name, path=dest)
    if models_dir is not None:
        patch_models_dir(profile.config_path, models_dir)
    return profile


def site_config_path_from_env(root: Path | None = None) -> Path | None:
    """If ``EZRA_SITE`` is set and has ezra.yaml, return that path."""
    try:
        site = current_site(root)
    except (FileNotFoundError, ValueError):
        return None
    if site and site.config_path.is_file():
        return site.config_path
    return None
