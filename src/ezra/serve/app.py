"""OpenAI-compatible FastAPI app for ``ezra serve``."""

from __future__ import annotations

import json
import time
import uuid
from typing import Annotated, Any, Iterator

from ezra.conversation import Message, Session, open_session
from ezra.conversation.backends import ChatBackend
from ezra.gallery import ModelGallery

try:
    from fastapi import Body, FastAPI, HTTPException
    from fastapi.responses import JSONResponse, StreamingResponse
    from pydantic import BaseModel, ConfigDict, Field

    _SERVE_IMPORT_ERROR: Exception | None = None
except ImportError as _exc:  # pragma: no cover
    Body = Any  # type: ignore[misc,assignment]
    FastAPI = Any  # type: ignore[misc,assignment]
    HTTPException = Any  # type: ignore[misc,assignment]
    JSONResponse = Any  # type: ignore[misc,assignment]
    StreamingResponse = Any  # type: ignore[misc,assignment]
    BaseModel = object  # type: ignore[misc,assignment]
    ConfigDict = dict  # type: ignore[misc,assignment]

    def Field(*_a: Any, **_k: Any) -> None:  # type: ignore[misc,no-redef]
        return None

    _SERVE_IMPORT_ERROR = _exc


if _SERVE_IMPORT_ERROR is None:

    class ChatMessage(BaseModel):
        role: str
        content: str

    class ChatCompletionRequest(BaseModel):
        model_config = ConfigDict(protected_namespaces=())

        model: str | None = None
        messages: list[ChatMessage] = Field(default_factory=list)
        stream: bool = False
        temperature: float | None = None
        max_tokens: int | None = None

else:  # pragma: no cover

    class ChatMessage:  # type: ignore[no-redef]
        pass

    class ChatCompletionRequest:  # type: ignore[no-redef]
        pass


def parse_model_field(model: str | None) -> tuple[str | None, str | None]:
    """Parse request ``model`` into ``(agent_name, gallery_alias)``.

    ``agent:chem-assistant`` → agent binding. Plain gallery names → model only.
    """
    if model is None or not str(model).strip():
        return None, None
    raw = str(model).strip()
    if raw.lower().startswith("agent:"):
        return raw.split(":", 1)[1].strip() or None, None
    return None, raw


def fastapi_available() -> bool:
    return _SERVE_IMPORT_ERROR is None


def _sse_chat_chunks(
    *,
    session: Session,
    user_text: str,
    model_id: str,
    completion_id: str,
    created: int,
) -> Iterator[str]:
    for chunk in session.stream(user_text):
        payload = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": chunk},
                    "finish_reason": None,
                }
            ],
        }
        yield f"data: {json.dumps(payload)}\n\n"
    done = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model_id,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(done)}\n\n"
    yield "data: [DONE]\n\n"


def create_app(
    *,
    backend: ChatBackend,
    default_agent: str | None = None,
    default_model: str | None = None,
    gallery: ModelGallery | None = None,
    backend_label: str = "local",
    root: Any = None,
    config: Any = None,
) -> Any:
    """Build a FastAPI app exposing ``/v1/models`` and ``/v1/chat/completions``."""
    if _SERVE_IMPORT_ERROR is not None:
        raise RuntimeError(
            "FastAPI/uvicorn not installed. "
            "Install the serve extra: pip install -e '.[serve]'"
        ) from _SERVE_IMPORT_ERROR

    gal = gallery or ModelGallery()
    app = FastAPI(title="EZRA", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/models")
    def list_models() -> dict[str, Any]:
        data: list[dict[str, Any]] = []
        for name in gal.names():
            data.append(
                {
                    "id": name,
                    "object": "model",
                    "owned_by": "ezra",
                }
            )
        if default_agent:
            data.insert(
                0,
                {
                    "id": f"agent:{default_agent}",
                    "object": "model",
                    "owned_by": "ezra",
                },
            )
        return {"object": "list", "data": data}

    def _session_for_request(req: ChatCompletionRequest) -> tuple[Session, str, str | None]:
        agent_from_model, model_from_field = parse_model_field(req.model)
        agent = agent_from_model or default_agent
        model = model_from_field or (None if agent else default_model)
        if not agent and not model:
            raise HTTPException(
                status_code=400,
                detail="Provide model (gallery alias or agent:<name>) "
                "or start serve with --agent / --model.",
            )
        session = open_session(
            agent=agent,
            model=model,
            backend=backend,
            root=root,
            config=config,
        )
        session._messages.clear()
        for msg in req.messages:
            role = msg.role if msg.role in ("system", "user", "assistant") else "user"
            session._messages.append(Message(role=role, content=msg.content))  # type: ignore[arg-type]
        if not session._messages or session._messages[-1].role != "user":
            raise HTTPException(
                status_code=400,
                detail="messages must end with a user turn.",
            )
        model_id = req.model or (f"agent:{agent}" if agent else model) or session.model
        return session, str(model_id), agent

    @app.post("/v1/chat/completions")
    def chat_completions(
        req: Annotated[ChatCompletionRequest, Body()],
    ) -> Any:
        session, model_id, agent = _session_for_request(req)
        last = session._messages.pop()
        user_text = last.content
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        created = int(time.time())
        ezra_meta = {
            "agent": agent or session.agent,
            "backend": backend_label,
            "resolved_model": session.model,
        }

        if req.stream:

            def gen() -> Iterator[str]:
                yield from _sse_chat_chunks(
                    session=session,
                    user_text=user_text,
                    model_id=model_id,
                    completion_id=completion_id,
                    created=created,
                )

            return StreamingResponse(gen(), media_type="text/event-stream")

        reply = session.send(user_text)
        body = {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": reply.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": reply.text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "ezra": ezra_meta,
        }
        return JSONResponse(body)

    return app


def run_server(
    app: Any,
    *,
    host: str = "0.0.0.0",
    port: int = 8000,
) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="info")
