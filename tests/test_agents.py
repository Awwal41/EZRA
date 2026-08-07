"""Tests for personal agent profiles."""

from __future__ import annotations

from pathlib import Path

import pytest

from ezra.agents import (
    AgentSpec,
    check_agent_models,
    get_agent,
    init_agent,
    list_agents,
    load_agent_spec,
    validate_agent_name,
)


def _fake_agents_tree(tmp_path: Path) -> Path:
    agents = tmp_path / "agents"
    template = agents / "_template"
    template.mkdir(parents=True)
    (template / "agent.yaml").write_text(
        "version: 1\nname: my-agent\ndescription: stub\n"
        "models:\n  preferred:\n    - qwen2.5-7b-instruct\n"
        "  fallback: []\n  tags: []\n"
        "prompt: prompt.md\nscience_focus:\n  - general\ntools: []\n",
        encoding="utf-8",
    )
    (template / "prompt.md").write_text("# hello\n", encoding="utf-8")
    (template / "NOTES.md").write_text("# notes\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='ezra'\n", encoding="utf-8")
    return tmp_path


def test_validate_agent_name() -> None:
    assert validate_agent_name("lab-bot") == "lab-bot"
    assert validate_agent_name("local/scratch") == "local/scratch"
    with pytest.raises(ValueError):
        validate_agent_name("_template")
    with pytest.raises(ValueError):
        validate_agent_name("../evil")
    with pytest.raises(ValueError):
        validate_agent_name("a/b/c")


def test_init_agent_copies_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _fake_agents_tree(tmp_path)
    monkeypatch.setenv("EZRA_ROOT", str(root))

    profile = init_agent("demo-bot", root=root)
    assert profile.path.is_dir()
    assert profile.config_path.is_file()
    assert profile.prompt_path.is_file()
    spec = load_agent_spec(profile)
    assert spec.name == "demo-bot"
    assert list_agents(root)[0].name == "demo-bot"

    with pytest.raises(FileExistsError):
        init_agent("demo-bot", root=root)

    init_agent("demo-bot", root=root, force=True, description="Office hours")
    spec2 = load_agent_spec(get_agent("demo-bot", root=root))
    assert "Office hours" in spec2.description


def test_init_agent_local_nested(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _fake_agents_tree(tmp_path)
    monkeypatch.setenv("EZRA_ROOT", str(root))
    profile = init_agent("local/private-bot", root=root)
    assert profile.name == "local/private-bot"
    assert (root / "agents" / "local" / "private-bot" / "agent.yaml").is_file()
    names = [p.name for p in list_agents(root)]
    assert "local/private-bot" in names


def test_check_agent_models() -> None:
    spec = AgentSpec(
        name="x",
        preferred_models=["chemllm-7b", "nope-model"],
        fallback_models=["phi-3.5-mini-instruct"],
    )
    result = check_agent_models(
        spec,
        {"chemllm-7b", "phi-3.5-mini-instruct", "qwen2.5-7b-instruct"},
        prompt_exists=True,
    )
    assert result.known == ["chemllm-7b", "phi-3.5-mini-instruct"]
    assert result.unknown == ["nope-model"]
    assert result.download_hint and "chemllm-7b" in result.download_hint
    assert not result.missing_prompt
