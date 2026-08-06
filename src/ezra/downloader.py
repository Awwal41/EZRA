"""Download curated free models from Hugging Face (HPC-friendly)."""

from __future__ import annotations

import json
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from huggingface_hub import hf_hub_download, snapshot_download
from huggingface_hub.utils import GatedRepoError, HfHubHTTPError, RepositoryNotFoundError

from ezra.config import EzraConfig
from ezra.gallery import ModelGallery, ModelSpec

ProgressCb = Callable[[str], None]


@dataclass
class DownloadResult:
    name: str
    repo_id: str
    path: str
    status: str  # downloaded | skipped | failed | already_present
    message: str = ""
    seconds: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class ModelDownloader:
    """Download one or many gallery models into the EZRA models directory."""

    def __init__(
        self,
        config: EzraConfig,
        gallery: ModelGallery | None = None,
        *,
        on_log: ProgressCb | None = None,
    ) -> None:
        self.config = config
        self.gallery = gallery or ModelGallery()
        self.on_log = on_log or (lambda _msg: None)
        self.models_dir = Path(config.models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.models_dir / "manifest.json"

    def _log(self, message: str) -> None:
        self.on_log(message)

    def model_dir(self, spec: ModelSpec) -> Path:
        return self.models_dir / spec.name

    def is_installed(self, spec: ModelSpec) -> bool:
        target = self.model_dir(spec)
        if not target.exists():
            return False
        # Any non-empty content (excluding marker) counts as present
        for path in target.rglob("*"):
            if path.is_file() and path.name != ".ezra_incomplete":
                return True
        return False

    def local_path(self, name: str) -> Path | None:
        try:
            spec = self.gallery.get(name)
        except KeyError:
            return None
        path = self.model_dir(spec)
        return path if self.is_installed(spec) else None

    def list_installed(self) -> list[ModelSpec]:
        return [s for s in self.gallery.list() if self.is_installed(s)]

    def _token(self) -> str | None:
        return self.config.hf_token

    def _allow_patterns(self, spec: ModelSpec, quant: str | None) -> list[str] | None:
        if spec.files:
            return list(spec.files)
        preferred = (quant or self.config.prefer_quant or spec.quant or "auto").strip()
        if preferred.lower() == "auto":
            preferred = spec.quant

        if spec.file_pattern:
            # Support "a|b|c" style patterns from gallery YAML
            patterns = [p.strip() for p in str(spec.file_pattern).split("|") if p.strip()]
            if preferred and preferred.lower() != "auto" and spec.format == "gguf":
                # Prefer exact quant if user overrode
                quant_pat = f"*{preferred}*"
                if quant_pat not in patterns:
                    patterns = [quant_pat, *patterns]
            return patterns

        if spec.format == "gguf":
            return [f"*{preferred}*", "*.md", "*.json", "*.txt"]
        return None

    def download_one(
        self,
        name: str,
        *,
        quant: str | None = None,
        force: bool = False,
        dry_run: bool = False,
    ) -> DownloadResult:
        started = time.perf_counter()
        try:
            spec = self.gallery.get(name)
        except KeyError as exc:
            return DownloadResult(
                name=name,
                repo_id="",
                path="",
                status="failed",
                message=str(exc),
                seconds=time.perf_counter() - started,
            )

        target = self.model_dir(spec)
        if self.is_installed(spec) and not force:
            msg = f"Already present at {target}"
            self._log(f"[skip] {spec.name}: {msg}")
            return DownloadResult(
                name=spec.name,
                repo_id=spec.repo_id,
                path=str(target),
                status="already_present",
                message=msg,
                seconds=time.perf_counter() - started,
            )

        if dry_run:
            msg = f"Would download {spec.repo_id} -> {target}"
            self._log(f"[dry-run] {spec.name}: {msg}")
            return DownloadResult(
                name=spec.name,
                repo_id=spec.repo_id,
                path=str(target),
                status="skipped",
                message=msg,
                seconds=time.perf_counter() - started,
            )

        if spec.gated and not self._token():
            msg = (
                f"Model is gated. Set {self.config.hf_token_env} "
                "(and accept the license on Hugging Face), then retry."
            )
            self._log(f"[fail] {spec.name}: {msg}")
            return DownloadResult(
                name=spec.name,
                repo_id=spec.repo_id,
                path=str(target),
                status="failed",
                message=msg,
                seconds=time.perf_counter() - started,
            )

        target.mkdir(parents=True, exist_ok=True)
        marker = target / ".ezra_incomplete"
        marker.write_text("downloading\n", encoding="utf-8")
        self._log(f"[download] {spec.name} from {spec.repo_id} -> {target}")

        try:
            allow = self._allow_patterns(spec, quant)
            token = self._token()
            common = dict(
                repo_id=spec.repo_id,
                revision=spec.revision,
                token=token,
                local_dir=str(target),
            )

            if spec.files:
                for filename in spec.files:
                    hf_hub_download(filename=filename, **common)
            else:
                kwargs = dict(common)
                if allow:
                    kwargs["allow_patterns"] = allow
                # Avoid downloading giant LFS blobs we do not need when patterns set
                snapshot_download(**kwargs)

            if marker.exists():
                marker.unlink()
            self._update_manifest(spec, target)
            msg = f"Saved to {target}"
            self._log(f"[ok] {spec.name}: {msg}")
            return DownloadResult(
                name=spec.name,
                repo_id=spec.repo_id,
                path=str(target),
                status="downloaded",
                message=msg,
                seconds=time.perf_counter() - started,
            )
        except GatedRepoError as exc:
            msg = (
                f"Gated repo access denied. Accept the license on Hugging Face "
                f"and set {self.config.hf_token_env}. ({exc})"
            )
            self._log(f"[fail] {spec.name}: {msg}")
            return DownloadResult(
                name=spec.name,
                repo_id=spec.repo_id,
                path=str(target),
                status="failed",
                message=msg,
                seconds=time.perf_counter() - started,
            )
        except (RepositoryNotFoundError, HfHubHTTPError, OSError, ValueError) as exc:
            msg = str(exc)
            self._log(f"[fail] {spec.name}: {msg}")
            return DownloadResult(
                name=spec.name,
                repo_id=spec.repo_id,
                path=str(target),
                status="failed",
                message=msg,
                seconds=time.perf_counter() - started,
            )

    def download_many(
        self,
        names: list[str] | None = None,
        *,
        all_models: bool = False,
        tag: str | None = None,
        science_only: bool = False,
        include_gated: bool = False,
        max_size_b: float | None = None,
        format: str | None = None,
        quant: str | None = None,
        force: bool = False,
        dry_run: bool = False,
        workers: int | None = None,
    ) -> list[DownloadResult]:
        if all_models or names is None:
            specs = self.gallery.list(
                tag=tag,
                science_only=science_only,
                include_gated=include_gated,
                max_size_b=max_size_b,
                format=format,
            )
        else:
            specs = self.gallery.resolve_many(names)
            if tag:
                specs = [s for s in specs if tag.lower() in s.all_tags]
            if not include_gated:
                specs = [s for s in specs if not s.gated]

        if not specs:
            self._log("No models matched the selection.")
            return []

        self._log(f"Selected {len(specs)} model(s): {', '.join(s.name for s in specs)}")
        n_workers = max(1, workers or self.config.max_workers)

        # Sequential for a single model; parallel for bulk HPC pre-staging
        if len(specs) == 1 or n_workers == 1:
            return [
                self.download_one(s.name, quant=quant, force=force, dry_run=dry_run)
                for s in specs
            ]

        results: list[DownloadResult] = []
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            futures = {
                pool.submit(
                    self.download_one,
                    s.name,
                    quant=quant,
                    force=force,
                    dry_run=dry_run,
                ): s.name
                for s in specs
            }
            for fut in as_completed(futures):
                results.append(fut.result())
        results.sort(key=lambda r: r.name)
        return results

    def remove(self, name: str, *, dry_run: bool = False) -> DownloadResult:
        try:
            spec = self.gallery.get(name)
        except KeyError as exc:
            return DownloadResult(
                name=name, repo_id="", path="", status="failed", message=str(exc)
            )
        target = self.model_dir(spec)
        if not target.exists():
            return DownloadResult(
                name=spec.name,
                repo_id=spec.repo_id,
                path=str(target),
                status="skipped",
                message="Not installed",
            )
        if dry_run:
            return DownloadResult(
                name=spec.name,
                repo_id=spec.repo_id,
                path=str(target),
                status="skipped",
                message=f"Would remove {target}",
            )
        shutil.rmtree(target)
        self._remove_from_manifest(spec.name)
        return DownloadResult(
            name=spec.name,
            repo_id=spec.repo_id,
            path=str(target),
            status="downloaded",
            message=f"Removed {target}",
        )

    def _load_manifest(self) -> dict:
        if not self.manifest_path.exists():
            return {"models": {}}
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"models": {}}

    def _update_manifest(self, spec: ModelSpec, path: Path) -> None:
        data = self._load_manifest()
        models = data.setdefault("models", {})
        models[spec.name] = {
            "repo_id": spec.repo_id,
            "path": str(path),
            "format": spec.format,
            "quant": spec.quant,
            "license": spec.license,
            "science_tags": list(spec.science_tags),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def _remove_from_manifest(self, name: str) -> None:
        data = self._load_manifest()
        models = data.get("models") or {}
        if name in models:
            del models[name]
            self.manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def disk_usage(path: Path) -> int:
    """Total bytes under path."""
    total = 0
    if not path.exists():
        return 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                continue
    return total
