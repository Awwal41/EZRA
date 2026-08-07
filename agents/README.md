# Personal agents (build your own on EZRA)

EZRA already helps you **pick and download** free/open models. Personal agents
let you wrap that stack with **your** system prompt, preferred models, and
domain focus - so a materials postdoc, a chemistry undergrad, and a lab
automation script can each have a different assistant without forking EZRA.

Same idea as [site profiles](../sites/README.md) for HPC: copy a template, edit a few
files, optionally commit and share.

## Quick start

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
```

Point `models.preferred` at aliases from `ezra models list` / `ezra models recommend`,
then download what you need:

```bash
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
ezra agents init local/scratch-bot   # also fine: name starting without _
# or manually: mkdir -p agents/local && cp -r agents/_template agents/local/mine
```

`agents/local/` is gitignored (see `.gitignore`). Do not put HF tokens or private
data in tracked agent folders.

## Example

[`chem-assistant`](chem-assistant/) is a starter chemistry / materials profile:
preferred science models, a domain prompt, and notes. Copy it or start fresh
with `ezra agents init`.

## Roadmap

Phase 1 ships the **scaffold + validation** (`init` / `list` / `show` / `check`).
When local serve + routing land, the same `agent.yaml` will select models and
inject `prompt.md` into chat / API sessions - no re-scaffold required.

Full guide: [docs/agents.md](../docs/agents.md).
