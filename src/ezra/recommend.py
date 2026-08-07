"""Rank gallery models that fit the local machine."""

from __future__ import annotations

from dataclasses import dataclass

from ezra.gallery import ModelGallery, ModelSpec
from ezra.hardware import SystemInfo


@dataclass(frozen=True)
class Recommendation:
    spec: ModelSpec
    score: float
    required_gb: float
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "name": self.spec.name,
            "repo_id": self.spec.repo_id,
            "format": self.spec.format,
            "params": self.spec.params,
            "size_b": self.spec.size_b,
            "required_gb": self.required_gb,
            "score": round(self.score, 2),
            "reasons": list(self.reasons),
            "gated": self.spec.gated,
            "tags": list(self.spec.tags),
            "science_tags": list(self.spec.science_tags),
            "description": self.spec.description,
        }


def estimate_required_gb(spec: ModelSpec) -> float:
    """Return RAM/VRAM guidance in GB for a gallery model."""
    if spec.recommended_ram_gb is not None:
        return float(spec.recommended_ram_gb)
    size = spec.size_b or 1.0
    fmt = (spec.format or "").lower()
    if fmt == "gguf":
        return max(1.0, round(size * 0.6, 1))
    if fmt == "mlx":
        return max(1.0, round(size * 0.7, 1))
    # safetensors / bf16-ish
    return max(1.0, round(size * 2.0, 1))


def _keyword_bonus(spec: ModelSpec, keyword: str | None) -> tuple[float, list[str]]:
    if not keyword:
        return 0.0, []
    q = keyword.strip().lower()
    if not q:
        return 0.0, []

    reasons: list[str] = []
    bonus = 0.0
    name = spec.name.lower()
    tags = spec.all_tags
    desc = (spec.description or "").lower()

    if q in name or name.startswith(q) or q.replace(" ", "-") in name:
        bonus += 40.0
        reasons.append(f"name matches '{keyword}'")
    if q in tags or any(q in t for t in tags):
        bonus += 35.0
        reasons.append(f"tag matches '{keyword}'")
    if q in desc or all(part in desc for part in q.split()):
        bonus += 15.0
        if not reasons:
            reasons.append(f"description matches '{keyword}'")
    elif not reasons and spec.matches_query(keyword):
        bonus += 10.0
        reasons.append(f"matched '{keyword}'")

    return bonus, reasons


def _format_bonus(spec: ModelSpec, system: SystemInfo) -> tuple[float, list[str]]:
    fmt = (spec.format or "").lower()
    reasons: list[str] = []
    bonus = 0.0

    if system.has_gpu:
        if fmt == "safetensors":
            bonus += 8.0
            reasons.append("GPU-friendly safetensors")
        elif fmt == "gguf":
            bonus += 4.0
    else:
        if fmt == "gguf":
            bonus += 20.0
            reasons.append("preferred GGUF on CPU")
        elif "local" in spec.all_tags:
            bonus += 10.0
            reasons.append("local-friendly")
        elif fmt == "safetensors" and spec.size_b <= 0.5:
            bonus += 5.0
            reasons.append("small encoder fits CPU")
        elif fmt == "safetensors" and spec.size_b > 1.0:
            bonus -= 25.0
            reasons.append("large safetensors without GPU")

    return bonus, reasons


def recommend(
    gallery: ModelGallery,
    system: SystemInfo,
    *,
    keyword: str | None = None,
    tag: str | None = None,
    science_only: bool = False,
    include_gated: bool = False,
    format: str | None = None,
    limit: int = 5,
) -> list[Recommendation]:
    """Return ranked models that fit ``system`` for an optional keyword."""
    budget = system.effective_memory_gb
    candidates = gallery.list(
        query=keyword,
        tag=tag,
        science_only=science_only,
        include_gated=include_gated,
        format=format,
    )

    ranked: list[Recommendation] = []
    for spec in candidates:
        required = estimate_required_gb(spec)
        if budget > 0 and required > budget:
            continue
        # If we could not measure memory, still recommend but note uncertainty
        reasons: list[str] = []
        score = 0.0

        if budget <= 0:
            reasons.append("memory unknown; listed without fit filter")
        else:
            utilization = required / budget if budget else 0.0
            # Prefer near-capacity fills (optimal use), not the tiniest model
            score += 50.0 * utilization
            mem_label = "VRAM" if system.has_gpu else "RAM"
            reasons.append(f"fits {required:.0f} GB need in {budget:.1f} GB {mem_label}")

        kw_bonus, kw_reasons = _keyword_bonus(spec, keyword)
        score += kw_bonus
        reasons.extend(kw_reasons)

        fmt_bonus, fmt_reasons = _format_bonus(spec, system)
        score += fmt_bonus
        reasons.extend(fmt_reasons)

        if not include_gated and spec.gated:
            continue
        if spec.gated:
            score -= 5.0
            reasons.append("gated HF license")

        # Slight preference for instruct / chat over encoders when no keyword
        if not keyword and "instruct" in spec.all_tags:
            score += 5.0

        ranked.append(
            Recommendation(
                spec=spec,
                score=score,
                required_gb=required,
                reasons=tuple(reasons),
            )
        )

    ranked.sort(key=lambda r: (-r.score, r.required_gb, r.spec.name))
    if limit > 0:
        return ranked[:limit]
    return ranked
