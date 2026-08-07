"""Tests for OpenAI-compatible serve helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from ezra.conversation import StubBackend
from ezra.serve.app import parse_model_field


def test_parse_model_field() -> None:
    assert parse_model_field(None) == (None, None)
    assert parse_model_field("qwen2.5-7b-instruct") == (None, "qwen2.5-7b-instruct")
    assert parse_model_field("agent:chem-assistant") == ("chem-assistant", None)
    assert parse_model_field("agent:") == (None, None)


def test_create_app_chat_completions() -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from ezra.serve.app import create_app

    app = create_app(
        backend=StubBackend(),
        default_model="phi-3.5-mini-instruct",
        backend_label="stub",
    )
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
    models = client.get("/v1/models").json()
    assert models["object"] == "list"
    assert any(m["id"] == "phi-3.5-mini-instruct" for m in models["data"])

    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "phi-3.5-mini-instruct",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["choices"][0]["message"]["content"] == "[stub:phi-3.5-mini-instruct] hello"
    assert body["ezra"]["backend"] == "stub"
    assert body["ezra"]["resolved_model"] == "phi-3.5-mini-instruct"


def test_create_app_agent_model_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from ezra.agents import init_agent
    from ezra.serve.app import create_app

    agents = tmp_path / "agents"
    template = agents / "_template"
    template.mkdir(parents=True)
    (template / "agent.yaml").write_text(
        "version: 1\nname: my-agent\ndescription: stub\n"
        "models:\n  preferred:\n    - phi-3.5-mini-instruct\n"
        "  fallback: []\n  tags: []\n"
        "prompt: prompt.md\nscience_focus:\n  - general\ntools: []\n",
        encoding="utf-8",
    )
    (template / "prompt.md").write_text("You are helpful.\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='ezra'\n", encoding="utf-8")
    monkeypatch.setenv("EZRA_ROOT", str(tmp_path))
    init_agent("demo", root=tmp_path)

    app = create_app(
        backend=StubBackend(),
        default_agent="demo",
        backend_label="stub",
        root=tmp_path,
    )
    client = TestClient(app)
    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "agent:demo",
            "messages": [{"role": "user", "content": "hi"}],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "hi" in body["choices"][0]["message"]["content"]
    assert body["ezra"]["agent"] == "demo"
