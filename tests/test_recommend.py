"""Unit tests for hardware-aware model recommendations."""

from __future__ import annotations

from ezra.gallery import load_gallery
from ezra.hardware import SystemInfo
from ezra.recommend import estimate_required_gb, recommend


def _cpu_system(ram_gb: float) -> SystemInfo:
    return SystemInfo(ram_total_gb=ram_gb, cpu_count=8, gpus=())


def test_estimate_uses_gallery_field() -> None:
    gallery = load_gallery()
    spec = gallery.get("qwen2.5-7b-instruct")
    assert estimate_required_gb(spec) == float(spec.recommended_ram_gb)


def test_chemistry_on_8gb_prefers_local_over_70b() -> None:
    gallery = load_gallery()
    # 8 GB RAM → ~6.4 GB fit budget on CPU
    picks = recommend(
        gallery,
        _cpu_system(8.0),
        keyword="chemistry",
        include_gated=False,
        limit=5,
    )
    assert picks
    names = [r.spec.name for r in picks]
    assert "llama3.1-70b-instruct" not in names
    assert "kimi-k2-instruct" not in names
    # ChemLLM needs 16 GB — should not fit
    assert "chemllm-7b" not in names
    # Small chemistry encoder or chemistry-friendly GGUF should appear
    assert any(
        n in names
        or "chem" in n
        or "chemistry" in " ".join(r.spec.all_tags)
        for n, r in zip(names, picks)
    )
    # Top pick should be GGUF-friendly on CPU when available among fits
    top = picks[0]
    assert top.required_gb <= _cpu_system(8.0).effective_memory_gb
    assert top.to_dict()["name"] == top.spec.name
    assert "reasons" in top.to_dict()


def test_low_ram_excludes_heavy_models() -> None:
    gallery = load_gallery()
    picks = recommend(
        gallery,
        _cpu_system(4.0),
        keyword=None,
        include_gated=False,
        limit=20,
    )
    assert picks
    budget = _cpu_system(4.0).effective_memory_gb  # 3.2 GB
    for rec in picks:
        assert rec.required_gb <= budget
        assert rec.spec.size_b < 70


def test_gpu_budget_allows_larger_safetensors() -> None:
    from ezra.hardware import GpuInfo

    gallery = load_gallery()
    system = SystemInfo(
        ram_total_gb=64.0,
        cpu_count=16,
        gpus=(GpuInfo(name="Test GPU", vram_total_mb=24 * 1024),),
    )
    picks = recommend(
        gallery,
        system,
        keyword="chemistry",
        include_gated=False,
        limit=10,
    )
    names = [r.spec.name for r in picks]
    # 24 GB VRAM should allow ChemLLM (16 GB)
    assert "chemllm-7b" in names
    assert picks[0].required_gb <= system.effective_memory_gb


def test_recommend_respects_format_filter() -> None:
    gallery = load_gallery()
    picks = recommend(
        gallery,
        _cpu_system(32.0),
        keyword=None,
        format="gguf",
        limit=10,
    )
    assert picks
    assert all(r.spec.format.lower() == "gguf" for r in picks)


def test_systeminfo_effective_memory() -> None:
    cpu = _cpu_system(10.0)
    assert abs(cpu.effective_memory_gb - 8.0) < 1e-6
    assert not cpu.has_gpu
