# Personal agents

Build your own assistant on top of EZRA: a **system prompt**, **preferred gallery models**, and optional domain focus — without forking the project.

Agents are folders under [`agents/`](../agents/README.md), same spirit as [HPC site profiles](../sites/README.md).

## Why

| You want… | Use |
|-----------|-----|
| Models that fit this laptop / node | `ezra models recommend` |
| Weights on disk | `ezra models download` |
| Your voice, domain, and model prefs | `ezra agents init` |

Phase 1 ships the **scaffold and checks**. When local serve + routing land, the same `agent.yaml` will drive which model answers and which prompt is injected.

## Quick start

```bash
pip install -e .
ezra agents init my-lab-assistant

# edit agents/my-lab-assistant/agent.yaml  (preferred models)
# edit agents/my-lab-assistant/prompt.md   (system prompt)

ezra agents list
ezra agents show my-lab-assistant
ezra agents show my-lab-assistant --prompt
ezra agents check my-lab-assistant
```

Then align weights with your prefs:

```bash
ezra models recommend chemistry
ezra models download chemllm-7b qwen2.5-7b-instruct
```

## Commands

| Command | Description |
|---------|-------------|
| `ezra agents list` | Profiles under `agents/` (including `agents/local/…`) |
| `ezra agents init NAME` | Copy `agents/_template` → `agents/<NAME>` |
| `ezra agents show NAME` | Summary + prompt preview (`--prompt` for full text) |
| `ezra agents check NAME` | Validate aliases against the gallery; suggest downloads |

`init` flags: `--force`, `--description "…"`.

Names may be `my-bot` or `local/my-bot` (personal experiments under the gitignored `agents/local/` tree).

## Agent folder layout

```text
agents/
  _template/          # copied by ezra agents init
  chem-assistant/     # shipped example (chemistry / materials)
  my-lab-assistant/   # yours
    agent.yaml
    prompt.md
    NOTES.md
  local/              # gitignored — private only
    scratch-bot/
```

### `agent.yaml`

| Field | Meaning |
|-------|---------|
| `name` / `description` | Display metadata |
| `models.preferred` | Gallery aliases tried first |
| `models.fallback` | Used if preferred are missing / unfit |
| `models.tags` | Optional gallery tag hints (`chemistry`, …) |
| `prompt` | Relative path to the system prompt (default `prompt.md`) |
| `science_focus` | Domain labels for docs / future routing |
| `tools` | Reserved for Phase 3 tool hooks (leave `[]` for now) |

Use aliases from `ezra models list`. `ezra agents check` flags typos.

### `prompt.md`

Plain Markdown (or text) system prompt. Keep secrets and unpublished data out of tracked agents.

## Example: chem-assistant

EZRA ships [`agents/chem-assistant`](../agents/chem-assistant/) with chemistry-oriented prefs and prompt. Inspect it:

```bash
ezra agents show chem-assistant
ezra agents check chem-assistant
```

Copy ideas into a new profile (`ezra agents init …`) rather than editing the example in place if you plan to pull upstream updates.

## Personal vs shareable

- **Shareable:** commit `agents/<name>/` (no tokens, no private lab data).
- **Private:** `ezra agents init local/my-bot` → lives under `agents/local/` (gitignored).

## Related

- [Models](models.md) — recommend / download
- [Configuration](configuration.md) — `ezra.yaml`, env vars
- [CLI](cli.md) — full command list
- [agents/README.md](../agents/README.md) — short overview in-tree
