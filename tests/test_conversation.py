"""Tests for the conversation runtime (session binding + stub backend)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ezra.conversation import (
    Message,
    StubBackend,
    open_session,
    resolve_session_model,
    sessions_dir,
)


def _fake_agents_tree(tmp_path: Path) -> Path:
    agents = tmp_path / "agents"
    template = agents / "_template"
    template.mkdir(parents=True)
    (template / "agent.yaml").write_text(
        "version: 1\nname: my-agent\ndescription: stub\n"
        "models:\n  preferred:\n    - chemllm-7b\n"
        "    - qwen2.5-7b-instruct\n"
        "  fallback:\n    - phi-3.5-mini-instruct\n"
        "  tags: []\n"
        "prompt: prompt.md\nscience_focus:\n  - chemistry\ntools: []\n"
        "router:\n  mode: local_only\n",
        encoding="utf-8",
    )
    (template / "prompt.md").write_text(
        "You are a chemistry lab assistant.\n",
        encoding="utf-8",
    )
    (template / "NOTES.md").write_text("# notes\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='ezra'\n", encoding="utf-8")
    return tmp_path


def test_resolve_session_model_explicit() -> None:
    assert (
        resolve_session_model(
            explicit="phi-3.5-mini-instruct",
            preferred=["chemllm-7b"],
            fallback=["qwen2.5-7b-instruct"],
        )
        == "phi-3.5-mini-instruct"
    )


def test_resolve_session_model_prefers_available() -> None:
    assert (
        resolve_session_model(
            preferred=["chemllm-7b", "qwen2.5-7b-instruct"],
            fallback=["phi-3.5-mini-instruct"],
            available={"qwen2.5-7b-instruct", "phi-3.5-mini-instruct"},
        )
        == "qwen2.5-7b-instruct"
    )


def test_resolve_session_model_falls_back_when_none_installed() -> None:
    assert (
        resolve_session_model(
            preferred=["chemllm-7b"],
            fallback=["phi-3.5-mini-instruct"],
            available=set(),
        )
        == "chemllm-7b"
    )


def test_resolve_session_model_empty_raises() -> None:
    with pytest.raises(ValueError, match="No model"):
        resolve_session_model()


def test_open_session_requires_backend(tmp_path: Path) -> None:
    root = _fake_agents_tree(tmp_path)
    from ezra.agents import init_agent

    init_agent("lab-bot", root=root)
    with pytest.raises(RuntimeError, match="No chat backend"):
        open_session(agent="lab-bot", root=root)


def test_open_session_agent_injects_prompt_and_model(tmp_path: Path) -> None:
    root = _fake_agents_tree(tmp_path)
    from ezra.agents import init_agent

    init_agent("lab-bot", root=root)
    s = open_session(
        agent="lab-bot",
        root=root,
        backend=StubBackend(),
        available_models={"qwen2.5-7b-instruct"},
    )
    assert s.agent == "lab-bot"
    assert s.model == "qwen2.5-7b-instruct"
    assert s.router_mode == "local_only"
    assert s.messages[0]["role"] == "system"
    assert "chemistry lab assistant" in s.messages[0]["content"]

    reply = s.send("What is pH?")
    assert reply.agent == "lab-bot"
    assert reply.model == "qwen2.5-7b-instruct"
    assert reply.text == "[stub:qwen2.5-7b-instruct] What is pH?"
    assert s.messages[-2]["role"] == "user"
    assert s.messages[-1]["role"] == "assistant"


def test_open_session_model_only() -> None:
    s = open_session(model="phi-3.5-mini-instruct", backend=StubBackend())
    assert s.agent is None
    assert s.model == "phi-3.5-mini-instruct"
    assert s.messages == []
    reply = s.send("hi")
    assert reply.text == "[stub:phi-3.5-mini-instruct] hi"


def test_stream_accumulates_assistant(tmp_path: Path) -> None:
    s = open_session(
        model="chemllm-7b",
        backend=StubBackend(chunk_size=8),
    )
    chunks = list(s.stream("hello"))
    assert "".join(chunks) == "[stub:chemllm-7b] hello"
    assert len(chunks) > 1
    assert s.messages[-1] == {"role": "assistant", "content": "[stub:chemllm-7b] hello"}


def test_session_save(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EZRA_HOME", str(tmp_path / "home"))
    s = open_session(model="chemllm-7b", backend=StubBackend())
    s.send("ping")
    path = s.save()
    assert path == sessions_dir() / f"{s.id}.json"
    assert path.is_file()
    data = path.read_text(encoding="utf-8")
    assert "chemllm-7b" in data
    assert "ping" in data


def test_message_roundtrip() -> None:
    msg = Message.from_dict({"role": "user", "content": "x"})
    assert msg.to_dict() == {"role": "user", "content": "x"}
    with pytest.raises(ValueError):
        Message.from_dict({"role": "tool", "content": "x"})


def test_open_session_requires_agent_or_model() -> None:
    with pytest.raises(ValueError, match="agent"):
        open_session(backend=StubBackend())
