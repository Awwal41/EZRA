"""Curated free/open model gallery."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml


@dataclass(frozen=True)
class ModelSpec:
    name: str
    repo_id: str
    format: str = "gguf"
    quant: str = "Q4_K_M"
    size_b: float = 0.0
    params: str = ""
    license: str = "unknown"
    gated: bool = False
    science_tags: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    description: str = ""
    file_pattern: str | None = None
    files: tuple[str, ...] = ()
    revision: str | None = None
    recommended_ram_gb: float | None = None
    raw: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)

    @property
    def all_tags(self) -> set[str]:
        return {t.lower() for t in (*self.tags, *self.science_tags)}

    def matches_query(self, query: str) -> bool:
        q = query.strip().lower()
        if not q:
            return True
        haystack = " ".join(
            [
                self.name,
                self.repo_id,
                self.description,
                self.params,
                " ".join(self.tags),
                " ".join(self.science_tags),
            ]
        ).lower()
        return q in haystack or all(part in haystack for part in q.split())


def _gallery_path() -> Path:
    return Path(__file__).resolve().parent / "models.yaml"


def _as_tuple(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(v) for v in value)


def _parse_model(entry: dict[str, Any]) -> ModelSpec:
    name = str(entry["name"]).strip()
    if not name:
        raise ValueError("Model entry missing name")
    return ModelSpec(
        name=name,
        repo_id=str(entry["repo_id"]),
        format=str(entry.get("format", "gguf")),
        quant=str(entry.get("quant", "Q4_K_M")),
        size_b=float(entry.get("size_b") or 0.0),
        params=str(entry.get("params") or ""),
        license=str(entry.get("license") or "unknown"),
        gated=bool(entry.get("gated", False)),
        science_tags=_as_tuple(entry.get("science_tags")),
        tags=_as_tuple(entry.get("tags")),
        description=str(entry.get("description") or ""),
        file_pattern=entry.get("file_pattern"),
        files=_as_tuple(entry.get("files")),
        revision=entry.get("revision"),
        recommended_ram_gb=(
            float(entry["recommended_ram_gb"])
            if entry.get("recommended_ram_gb") is not None
            else None
        ),
        raw=entry,
    )


class ModelGallery:
    """Load and query the curated free-model catalog."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _gallery_path()
        self._models: dict[str, ModelSpec] = {}
        self.reload()

    def reload(self) -> None:
        with self.path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        entries = data.get("models") or []
        models: dict[str, ModelSpec] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            spec = _parse_model(entry)
            if spec.name in models:
                raise ValueError(f"Duplicate model name in gallery: {spec.name}")
            models[spec.name] = spec
        self._models = models

    def list(
        self,
        *,
        query: str | None = None,
        tag: str | None = None,
        science_only: bool = False,
        include_gated: bool = True,
        max_size_b: float | None = None,
        format: str | None = None,
    ) -> list[ModelSpec]:
        results: list[ModelSpec] = []
        for spec in self._models.values():
            if query and not spec.matches_query(query):
                continue
            if tag and tag.lower() not in spec.all_tags:
                continue
            if science_only and not spec.science_tags:
                continue
            if not include_gated and spec.gated:
                continue
            if max_size_b is not None and spec.size_b > max_size_b:
                continue
            if format and spec.format.lower() != format.lower():
                continue
            results.append(spec)
        results.sort(key=lambda m: (m.size_b, m.name))
        return results

    def get(self, name: str) -> ModelSpec:
        key = name.strip().lower()
        for spec in self._models.values():
            if spec.name.lower() == key:
                return spec
        # fuzzy: unique prefix / substring
        matches = [s for s in self._models.values() if key in s.name.lower()]
        if len(matches) == 1:
            return matches[0]
        if not matches:
            available = ", ".join(sorted(self._models))
            raise KeyError(
                f"Unknown model '{name}'. Available: {available or '(empty gallery)'}"
            )
        names = ", ".join(m.name for m in matches)
        raise KeyError(f"Ambiguous model '{name}'. Candidates: {names}")

    def names(self) -> list[str]:
        return sorted(self._models)

    def resolve_many(self, names: Iterable[str]) -> list[ModelSpec]:
        return [self.get(n) for n in names]


def load_gallery(path: Path | None = None) -> ModelGallery:
    return ModelGallery(path=path)
