# Personal agents (build your own on EZRA)

EZRA already helps you **pick and download** free/open models. Personal agents
let you wrap that stack with **your** system prompt, preferred models, and
domain focus - so a materials postdoc, a chemistry undergrad, and a lab
automation script can each have a different assistant without forking EZRA.

Same idea as [site profiles](../sites/README.md) for HPC: copy a template, edit a few
files, optionally commit and share.

**Full step-by-step guide:** [docs/agents.md](../docs/agents.md)
(install → init → recommend models → edit `agent.yaml` / `prompt.md` → check → download).

## Quick start (10 steps)

1. `pip install -e .` and `ezra doctor`
2. `ezra agents init my-lab-assistant` (or `local/scratch-bot` for private)
3. `ezra models recommend chemistry` (pick aliases that fit this machine)
4. Edit `agents/my-lab-assistant/agent.yaml` (`preferred` / `fallback` / tags)
5. Edit `prompt.md` (role, priorities, style, boundaries)
6. Fill `NOTES.md` (owner, hardware, intent)
7. `ezra agents check my-lab-assistant`
8. `ezra agents show my-lab-assistant --prompt`
9. `ezra models download <preferred-alias> ...`
10. Iterate; keep private experiments under `agents/local/`

```bash
# from the repo root, after pip install -e .
ezra agents init my-lab-assistant

# edit the generated files (search for CUSTOMIZE ME)
$EDITOR agents/my-lab-assistant/agent.yaml
$EDITOR agents/my-lab-assistant/prompt.md
$EDITOR agents/my-lab-assistant/NOTES.md

ezra agents list
ezra agents show my-lab-assistant
ezra agents check my-lab-assistant   # validate gallery aliases + suggest downloads
ezra models recommend chemistry
ezra models download qwen2.5-7b-instruct
```

## What lives in an agent folder

| File | Purpose |
|------|---------|
| `agent.yaml` | Name, description, preferred/fallback models, tags, science focus |
| `prompt.md` | System prompt the agent will use (runtime/router land in Phase 2+) |
| `NOTES.md` | Human notes for you / your lab (optional to share) |

## Personal vs shareable

| Location | Intent |
|----------|--------|
| `agents/<name>/` | Shareable profile (commit & PR if useful to others) |
| `agents/local/` | Gitignored - keep private experiments here |

```bash
ezra agents init local/scratch-bot
```

`agents/local/` is gitignored (see `.gitignore`). Do not put HF tokens or private
data in tracked agent folders.

## Effective customization tips

- Pin **preferred** to 2-3 gallery aliases from `ezra models recommend`, plus lighter **fallback**.
- Write a short structured prompt: role → priorities → tasks → style → boundaries.
- Never invent citations in the prompt instructions; tell the model to ask when context is missing.
- Run `ezra agents check` after every YAML change.
- Study [`chem-assistant`](chem-assistant/) with `ezra agents show chem-assistant --prompt`, then copy ideas into a new profile.

## Example

[`chem-assistant`](chem-assistant/) is a starter chemistry / materials profile:
preferred science models, a domain prompt, and notes. Copy it or start fresh
with `ezra agents init`.

## Runtime

`ezra agents init` / `list` / `show` / `check` scaffold and validate profiles.
The same `agent.yaml` + `prompt.md` already select models and inject the system
prompt for `ezra chat` / `ezra serve`. Phase 2 adds smarter domain routing on
top — no re-scaffold required.
Design contract: [`docs/conversation.md`](../docs/conversation.md).
