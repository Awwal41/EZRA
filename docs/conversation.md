# Conversation runtime

**Status:** session API, llama.cpp / MLX backends, `ezra chat`, and OpenAI
`ezra serve` are implemented. Install optional extras for real inference.

EZRA turns an agent profile into multi-turn chat and an OpenAI-compatible HTTP
surface so labs can connect Gradio, Open WebUI, Cursor, or a custom UI without
forking EZRA.

See also: [Getting started](getting-started.md) (which llama.cpp **wheel**),
[Personal agents](agents.md), [Install](install.md), [CLI](cli.md),
[TODO.md](../TODO.md), [API](api.rst).

---

## Layers

| Layer | Role | Today |
|-------|------|--------|
| **Agents** (`agents/<name>/`) | Config: system prompt, preferred models, tools | Scaffold + checks |
| **Conversation** (`ezra.conversation`) | Sessions, history, agent binding, stream/send | Shipped |
| **Inference** (`ezra.inference`) | llama.cpp (GGUF), MLX, model cache | Optional extras |
| **Serve** (`ezra serve`) | OpenAI-compatible `/v1/chat/completions` | `pip install -e ".[serve]"` |
| **External UI** | Gradio, Open WebUI, lab frontends | Client only |

Agents stay YAML + Markdown. Conversation is the runtime. Frontends talk HTTP
(or the Python session API) — they do not invent their own prompt format.

---

## Install extras

```bash
pip install -r requirements-ide-cpu.txt   # GGUF + OpenAI HTTP (Windows/Linux CPU wheel)
# pip install -r requirements-ide-cuda124.txt
# pip install -r requirements-ide-macos.txt
# or, may compile from source: pip install -e ".[local,serve]"
```

Local chat needs a **downloaded GGUF** gallery model (`ezra models list --format gguf`).

---

## Python surface

```python
from ezra.conversation import open_session

# Auto-creates LocalRuntime when llama-cpp-python / mlx-lm is installed
s = open_session(agent="chem-assistant")
# Or: open_session(model="qwen2.5-7b-instruct")

reply = s.send("Explain this reaction…")
# reply.text, reply.model, reply.agent

for chunk in s.stream("…"):
    print(chunk, end="", flush=True)

s.messages   # [{role, content}, ...] including injected system prompt
s.save()     # ~/.ezra/sessions/<id>.json
```

Tests / dry-run: pass `backend=StubBackend()` or use `ezra chat --backend stub`.

### Binding rules

When `agent=` is set, load [`AgentSpec`](agents.md) and:

1. Inject `prompt.md` (or the path in `agent.yaml` → `prompt`) as the system message.
2. Resolve the first available model from `models.preferred`, then `models.fallback`.
3. Honor optional `router.mode` on the agent (else inherit `ezra.yaml`).

When only `model=` is set, use a default / empty system prompt and that gallery
alias.

---

## CLI

```bash
ezra chat --agent chem-assistant
ezra chat --model qwen2.5-7b-instruct
ezra chat --backend stub --model phi-3.5-mini-instruct -p "Hello"

ezra serve --agent chem-assistant --host 0.0.0.0 --port 8000
ezra serve --model qwen2.5-7b-instruct --host 0.0.0.0 --port 8000
```

HPC SBATCH templates call `ezra serve` when present ([HPC](hpc.md)):

```bash
ezra hpc submit serve --model qwen2.5-7b-instruct --gpus 1
```

(`--agent` on HPC submit is still a backlog idea; use `--model` or configure the agent’s preferred GGUF.)

---

## OpenAI-compatible HTTP

| Endpoint | Notes |
|----------|--------|
| `POST /v1/chat/completions` | Streaming + non-streaming |
| `GET /v1/models` | Gallery aliases and/or `agent:<name>` ids |
| `GET /health` | Liveness |

Clients set `base_url` to `http://<host>:<port>/v1`. The `model` field may be:

- a gallery alias (`qwen2.5-7b-instruct`), or
- an agent id (`agent:chem-assistant`) so the server applies that profile’s
  prompt and preferred-model chain.

Responses include `ezra.agent`, `ezra.backend`, and `ezra.resolved_model`.

---

## Connecting an interface

Any OpenAI-compatible client works once serve is up:

```python
# Example: point a lab UI or OpenAI SDK at EZRA
base_url = "http://localhost:8000/v1"
# model="agent:chem-assistant"  or  model="qwen2.5-7b-instruct"
```

**Open WebUI / Gradio:** set the OpenAI API base URL to your `ezra serve` host and
use a gallery alias or `agent:<name>` as the model id. No first-party Gradio app
is required for MVP.

**VS Code / Cursor:** sideload [EZRA Grid](ide.md) (`ezra ide install`). Local and
agent lanes call `ezra chat`. The Cline lane uses your downloaded models through
`ezra serve` (no cloud API key) — cookbook: [Cline + a free EZRA model](cline-local.md).

---

## Out of scope (for now)

- Visual workflow / multi-agent canvas
- Built-in multi-step science tool graphs (tools stay `[]` on agents until P2)
- Automatic safetensors → GGUF conversion
- Replacing the CLI or agent folder layout

## Package layout

- `src/ezra/conversation/` — sessions
- `src/ezra/inference/` — weights, llama.cpp / MLX, `LocalRuntime`
- `src/ezra/serve/` — FastAPI app factory
