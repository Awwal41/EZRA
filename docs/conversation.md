# Conversation runtime (design)

**Status:** session types + stub backend landed (`ezra.conversation`). Local
`ezra chat` / `ezra serve` still wait on inference backends.

EZRA Phase 1 scaffolds agents and downloads models. The **conversation** layer
is the thin runtime that turns an agent profile into multi-turn chat and (later)
an OpenAI-compatible HTTP surface so labs can connect Gradio, Open WebUI, Cursor,
or a custom UI without forking EZRA.

See also: [Personal agents](agents.md), [TODO.md](../TODO.md) (P0 serve / P1
wire-agents / sessions), [API](api.rst).

---

## Layers

| Layer | Role | Today |
|-------|------|--------|
| **Agents** (`agents/<name>/`) | Config: system prompt, preferred models, tools | Scaffold + checks |
| **Conversation** (`ezra.conversation`) | Sessions, history, agent binding, stream/send | Session API + `StubBackend` |
| **Serve** (`ezra serve`) | OpenAI-compatible `/v1/chat/completions` | Planned (P0) |
| **External UI** | Gradio, Open WebUI, lab frontends | Client only |

Agents stay YAML + Markdown. Conversation is the runtime. Frontends talk HTTP
(or the Python session API) — they do not invent their own prompt format.

---

## Python surface

```python
from ezra.conversation import StubBackend, open_session

# Prefer binding an existing agents/<name>/ profile.
# Until llama.cpp / MLX land, pass StubBackend() (tests / dry-run only).
s = open_session(agent="chem-assistant", backend=StubBackend())
# Or pin a gallery model without an agent:
# s = open_session(model="qwen2.5-7b-instruct", backend=StubBackend())

reply = s.send("Explain this reaction…")
# reply.text, reply.model, reply.agent

for chunk in s.stream("…"):
    print(chunk, end="", flush=True)

s.messages   # [{role, content}, ...] including injected system prompt
s.save()     # ~/.ezra/sessions/<id>.json
```

### Binding rules

When `agent=` is set, load [`AgentSpec`](agents.md) and:

1. Inject `prompt.md` (or the path in `agent.yaml` → `prompt`) as the system message.
2. Resolve the first available model from `models.preferred`, then `models.fallback`.
3. Honor optional `router.mode` on the agent (else inherit `ezra.yaml`).

When only `model=` is set, use a default / empty system prompt and that gallery
alias.

---

## CLI surface (target)

```bash
ezra chat --agent chem-assistant
ezra chat --model qwen2.5-7b-instruct

ezra serve --agent chem-assistant --host 0.0.0.0 --port 8000
ezra serve --model qwen2.5-7b-instruct --host 0.0.0.0 --port 8000
```

HPC SBATCH templates already call `ezra serve` when present
([HPC](hpc.md)). After this lands, prefer:

```bash
ezra hpc submit serve --agent chem-assistant --gpus 1
# or keep --model for a bare gallery alias
```

---

## OpenAI-compatible HTTP

`ezra serve` exposes at least:

| Endpoint | Notes |
|----------|--------|
| `POST /v1/chat/completions` | Streaming + non-streaming |
| `GET /v1/models` | Gallery aliases and/or `agent:<name>` ids |

Clients set `base_url` to `http://<host>:<port>/v1`. The `model` field may be:

- a gallery alias (`qwen2.5-7b-instruct`), or
- an agent id (`agent:chem-assistant`) so the server applies that profile’s
  prompt and preferred-model chain.

Response metadata should indicate **which model answered** (router / CLI
indicator from the P0 backlog).

---

## Connecting an interface

Any OpenAI-compatible client works once serve is up:

```python
# Example: point a lab UI or OpenAI SDK at EZRA
base_url = "http://localhost:8000/v1"
# model="agent:chem-assistant"  or  model="qwen2.5-7b-instruct"
```

No first-party Gradio/Streamlit app is required for MVP. A short recipe in
docs (Gradio or Open WebUI) is enough for P1/P2. A full desktop/web product UI
stays P2.

---

## Out of scope (for now)

- Visual workflow / multi-agent canvas
- Built-in multi-step science tool graphs (tools stay `[]` on agents until P2)
- Replacing the CLI or agent folder layout

---

## Ship order

1. **Session types** — done (`src/ezra/conversation/`, tests in `tests/test_conversation.py`).
2. **`ezra chat`** — once a local backend (llama.cpp / MLX) can complete.
3. **`ezra serve`** — `/v1/chat/completions` (+ streaming).
4. **Wire agents into serve** — same binding already used by `open_session`.
5. **Richer session notes** — optional experiment metadata beyond JSON save.
6. **Docs recipe** — “point Gradio / Open WebUI at EZRA”.

Package layout: `src/ezra/conversation/` — reused later by `cli.py` chat/serve.
