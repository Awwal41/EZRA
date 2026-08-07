"""Personal agent profiles under ``agents/<name>/``."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ezra.hpc.sites import repo_root

@dataclass(frozen=True)
class AgentProfile:
    name: str
    path: Path

    @property
    def config_path(self) -> Path:
        return self.path / "agent.yaml"

    @property
    def prompt_path(self) -> Path:
        """Resolve prompt file from agent.yaml ``prompt`` key (default ``prompt.md``)."""
        prompt_rel = "prompt.md"
        if self.config_path.is_file():
            try:
                data = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
                if isinstance(data, dict) and data.get("prompt"):
                    prompt_rel = str(data["prompt"])
            except (OSError, yaml.YAMLError):
                pass
        return self.path / prompt_rel

    @property
    def notes_path(self) -> Path:
        return self.path / "NOTES.md"


@dataclass
class AgentSpec:
    """Parsed ``agent.yaml`` contents."""

    name: str
    description: str = ""
    preferred_models: list[str] = field(default_factory=list)
    fallback_models: list[str] = field(default_factory=list)
    model_tags: list[str] = field(default_factory=list)
    science_focus: list[str] = field(default_factory=list)
    tools: list[Any] = field(default_factory=list)
    prompt_file: str = "prompt.md"
    router_mode: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def agents_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "agents"


def template_dir(root: Path | None = None) -> Path:
    return agents_dir(root) / "_template"


def validate_agent_name(name: str) -> str:
    name = name.strip().replace("\\", "/").strip("/")
    if not name:
        raise ValueError("Agent name must not be empty.")
    if name.startswith("_"):
        raise ValueError("Agent name must not start with '_' (reserved for templates).")
    if ".." in name.split("/"):
        raise ValueError(f"Invalid agent name: {name!r}")
    # Allow a single optional parent folder (e.g. local/my-bot)
    parts = name.split("/")
    if len(parts) > 2:
        raise ValueError(
            f"Invalid agent name {name!r}. Use 'name' or 'local/name' (at most one '/')."
        )
    for part in parts:
        if part in {".", ".."} or not part:
            raise ValueError(f"Invalid agent name: {name!r}")
        if part.startswith("_"):
            raise ValueError("Agent path segments must not start with '_'.")
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,62}$", part):
            raise ValueError(
                f"Invalid agent name {name!r}. "
                "Use letters, numbers, dots, dashes, underscores "
                "(optional 'local/' prefix)."
            )
    return name


def list_agents(root: Path | None = None) -> list[AgentProfile]:
    base = agents_dir(root)
    if not base.is_dir():
        return []
    profiles: list[AgentProfile] = []
    for child in sorted(base.iterdir()):
        if not child.is_dir() or child.name.startswith("_") or child.name.startswith("."):
            continue
        if child.name == "local":
            # Nested personal agents under agents/local/
            if child.is_dir():
                for nested in sorted(child.iterdir()):
                    if (
                        nested.is_dir()
                        and not nested.name.startswith("_")
                        and not nested.name.startswith(".")
                        and (nested / "agent.yaml").is_file()
                    ):
                        profiles.append(
                            AgentProfile(name=f"local/{nested.name}", path=nested)
                        )
            continue
        if (child / "agent.yaml").is_file():
            profiles.append(AgentProfile(name=child.name, path=child))
    return profiles


def get_agent(name: str, root: Path | None = None) -> AgentProfile:
    name = validate_agent_name(name)
    path = agents_dir(root) / name
    if not path.is_dir() or not (path / "agent.yaml").is_file():
        raise FileNotFoundError(
            f"Agent profile not found: {path}. "
            f"Create one with: ezra agents init {name}"
        )
    return AgentProfile(name=name, path=path)


def load_agent_spec(profile: AgentProfile) -> AgentSpec:
    path = profile.config_path
    if not path.is_file():
        raise FileNotFoundError(f"Missing agent.yaml: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"agent.yaml must be a mapping: {path}")

    models = data.get("models") or {}
    if not isinstance(models, dict):
        models = {}
    router = data.get("router") or {}
    if not isinstance(router, dict):
        router = {}

    preferred = models.get("preferred") or []
    fallback = models.get("fallback") or []
    tags = models.get("tags") or []
    focus = data.get("science_focus") or []
    tools = data.get("tools") or []

    return AgentSpec(
        name=str(data.get("name") or profile.name),
        description=str(data.get("description") or "").strip(),
        preferred_models=[str(x) for x in preferred],
        fallback_models=[str(x) for x in fallback],
        model_tags=[str(x) for x in tags],
        science_focus=[str(x) for x in focus],
        tools=list(tools) if isinstance(tools, list) else [],
        prompt_file=str(data.get("prompt") or "prompt.md"),
        router_mode=str(router["mode"]) if router.get("mode") else None,
        raw=data,
    )


def _patch_agent_identity(config_path: Path, name: str, display_name: str | None = None) -> None:
    """Set ``name:`` in agent.yaml to the folder / display name."""
    path = Path(config_path)
    text = path.read_text(encoding="utf-8")
    value = display_name or name.split("/")[-1]
    pattern = re.compile(r"^([ \t]*name:[ \t]*).*$", re.MULTILINE)
    if pattern.search(text):
        updated = pattern.sub(rf"\g<1>{value}", text, count=1)
    else:
        updated = f"name: {value}\n" + text
    path.write_text(updated, encoding="utf-8", newline="\n")


def init_agent(
    name: str,
    root: Path | None = None,
    *,
    force: bool = False,
    description: str | None = None,
) -> AgentProfile:
    """Copy ``agents/_template`` to ``agents/<name>``."""
    name = validate_agent_name(name)
    root = root or repo_root()
    src = template_dir(root)
    if not src.is_dir():
        raise FileNotFoundError(f"Missing template directory: {src}")
    dest = agents_dir(root) / name
    if dest.exists():
        if not force:
            raise FileExistsError(
                f"Agent already exists: {dest}. Use --force to overwrite, or pick another name."
            )
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)
    profile = AgentProfile(name=name, path=dest)
    _patch_agent_identity(profile.config_path, name)
    if description is not None:
        text = profile.config_path.read_text(encoding="utf-8")
        pattern = re.compile(r"^([ \t]*description:[ \t]*).*$", re.MULTILINE)
        if pattern.search(text):
            # Keep single-line descriptions simple
            safe = description.replace("\n", " ").strip()
            updated = pattern.sub(rf"\g<1>{safe}", text, count=1)
            profile.config_path.write_text(updated, encoding="utf-8", newline="\n")
    return profile


@dataclass
class AgentCheckResult:
    """Result of validating an agent against the gallery."""

    known: list[str]
    unknown: list[str]
    missing_prompt: bool
    download_hint: str | None = None


def check_agent_models(
    spec: AgentSpec,
    gallery_names: set[str] | list[str],
    *,
    prompt_exists: bool = True,
) -> AgentCheckResult:
    """Validate preferred/fallback aliases against the gallery."""
    names = set(gallery_names)
    ordered: list[str] = []
    seen: set[str] = set()
    for alias in [*spec.preferred_models, *spec.fallback_models]:
        if alias not in seen:
            ordered.append(alias)
            seen.add(alias)
    known = [a for a in ordered if a in names]
    unknown = [a for a in ordered if a not in names]
    hint = None
    if known:
        hint = f"ezra models download {' '.join(known[:3])}"
    return AgentCheckResult(
        known=known,
        unknown=unknown,
        missing_prompt=not prompt_exists,
        download_hint=hint,
    )
