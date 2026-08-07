"""Session binding: agent profiles → system prompt + model + chat turns."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Collection, Iterator, Sequence

from ezra.agents import AgentSpec, get_agent, load_agent_spec
from ezra.config import EzraConfig, default_home, load_config
from ezra.conversation.backends import ChatBackend
from ezra.conversation.types import Message, Reply


def resolve_session_model(
    *,
    explicit: str | None = None,
    preferred: Sequence[str] = (),
    fallback: Sequence[str] = (),
    available: Collection[str] | None = None,
) -> str:
    """Pick a gallery model alias for a session.

    Order:

    1. ``explicit`` if set
    2. First name in preferred → fallback that appears in ``available``
    3. Else first preferred → fallback (caller may download later)

    Raises:
        ValueError: nothing to resolve.
    """
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()
    chain = [str(x).strip() for x in (*preferred, *fallback) if str(x).strip()]
    if not chain:
        raise ValueError(
            "No model specified. Pass model=... or configure preferred/fallback "
            "models on the agent."
        )
    if available is not None:
        avail = set(available)
        for name in chain:
            if name in avail:
                return name
    return chain[0]


def _router_mode_from_config(config: EzraConfig | None) -> str:
    if config is None:
        return "auto"
    router = (config.raw or {}).get("router") or {}
    if isinstance(router, dict) and router.get("mode"):
        return str(router["mode"])
    return "auto"


def _installed_model_names(config: EzraConfig) -> set[str] | None:
    """Best-effort installed gallery names; ``None`` if probe fails."""
    try:
        from ezra.downloader import ModelDownloader

        return {s.name for s in ModelDownloader(config).list_installed()}
    except OSError:
        return None


def sessions_dir(home: Path | None = None) -> Path:
    """Directory for saved sessions (``~/.ezra/sessions``)."""
    return (home or default_home()) / "sessions"


@dataclass
class Session:
    """Multi-turn chat bound to an agent and/or gallery model.

    Use :func:`open_session` to construct. Pass a :class:`~ezra.conversation.backends.ChatBackend`
    (e.g. :class:`~ezra.conversation.backends.StubBackend` in tests); real
    inference backends are not shipped yet.
    """

    model: str
    backend: ChatBackend
    agent: str | None = None
    router_mode: str = "auto"
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    _messages: list[Message] = field(default_factory=list, repr=False)

    @property
    def messages(self) -> list[dict[str, str]]:
        """OpenAI-style message dicts (includes system prompt when present)."""
        return [m.to_dict() for m in self._messages]

    @property
    def message_objects(self) -> list[Message]:
        return list(self._messages)

    def send(self, text: str) -> Reply:
        """Append a user turn, complete via the backend, append assistant turn."""
        content = str(text)
        self._messages.append(Message(role="user", content=content))
        reply_text = self.backend.complete(self._messages, model=self.model)
        self._messages.append(Message(role="assistant", content=reply_text))
        return Reply(text=reply_text, model=self.model, agent=self.agent)

    def stream(self, text: str) -> Iterator[str]:
        """Append a user turn and stream the assistant reply (also stored)."""
        content = str(text)
        self._messages.append(Message(role="user", content=content))
        chunks: list[str] = []
        for chunk in self.backend.stream(self._messages, model=self.model):
            chunks.append(chunk)
            yield chunk
        reply_text = "".join(chunks)
        self._messages.append(Message(role="assistant", content=reply_text))

    def save(self, path: Path | None = None) -> Path:
        """Write session JSON under ``~/.ezra/sessions/<id>.json`` (or ``path``)."""
        dest = Path(path) if path is not None else sessions_dir() / f"{self.id}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "id": self.id,
            "agent": self.agent,
            "model": self.model,
            "router_mode": self.router_mode,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "messages": self.messages,
        }
        dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return dest


def open_session(
    *,
    agent: str | None = None,
    model: str | None = None,
    backend: ChatBackend | None = None,
    root: Path | None = None,
    config: EzraConfig | None = None,
    available_models: Collection[str] | None = None,
    system_prompt: str | None = None,
) -> Session:
    """Open a conversation session bound to an agent and/or gallery model.

    Args:
        agent: Name under ``agents/<name>/`` (loads prompt + preferred models).
        model: Gallery alias override (or sole binding when ``agent`` is omitted).
        backend: Completion backend. Required until local serve ships; use
            ``StubBackend()`` in tests.
        root: Repo root for agent lookup (tests).
        config: Loaded ``ezra.yaml`` (router defaults + optional install probe).
        available_models: If set, preferred/fallback resolution prefers these
            names. If omitted, probes installed models when possible.
        system_prompt: Override system text (skips reading ``prompt.md`` when set).

    Raises:
        ValueError: neither agent nor model given, or no model can be resolved.
        FileNotFoundError: agent profile missing.
        RuntimeError: no backend provided.
    """
    if not agent and not model:
        raise ValueError("Pass agent=... and/or model=... to open a session.")
    if backend is None:
        raise RuntimeError(
            "No chat backend configured. Local inference is not shipped yet. "
            "Pass StubBackend() for tests, or wait for ezra chat / ezra serve."
        )

    cfg = config
    agent_name: str | None = None
    spec: AgentSpec | None = None
    prompt_text = system_prompt
    preferred: list[str] = []
    fallback: list[str] = []
    router_mode = _router_mode_from_config(cfg)

    if agent:
        profile = get_agent(agent, root=root)
        spec = load_agent_spec(profile)
        agent_name = profile.name
        preferred = list(spec.preferred_models)
        fallback = list(spec.fallback_models)
        if spec.router_mode:
            router_mode = spec.router_mode
        if prompt_text is None and profile.prompt_path.is_file():
            prompt_text = profile.prompt_path.read_text(encoding="utf-8").strip()

    avail = available_models
    if avail is None and model is None:
        if cfg is None:
            try:
                cfg = load_config()
            except (OSError, ValueError):
                cfg = None
        if cfg is not None:
            avail = _installed_model_names(cfg)

    resolved = resolve_session_model(
        explicit=model,
        preferred=preferred,
        fallback=fallback,
        available=avail,
    )

    session = Session(
        model=resolved,
        backend=backend,
        agent=agent_name,
        router_mode=router_mode,
    )
    if prompt_text:
        session._messages.append(Message(role="system", content=prompt_text))
    return session
