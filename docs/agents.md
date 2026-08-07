# Personal agents

Build your own assistant on top of EZRA: a **system prompt**, **preferred gallery models**, and optional domain focus, without forking the project.

Agents are folders under [`agents/`](../agents/README.md), same spirit as [HPC site profiles](../sites/README.md).

Phase 1 ships the **scaffold and checks**. When local serve + routing land, the same `agent.yaml` will drive which model answers and which prompt is injected. Build agents carefully now so they keep working later. Design for that runtime: [Conversation runtime](conversation.md).

## Why use an agent

| You want... | Use |
|-----------|-----|
| Models that fit this laptop / node | `ezra models recommend` |
| Weights on disk | `ezra models download` |
| Your voice, domain, and model prefs in one reusable profile | `ezra agents init` |

One lab can keep several agents (teaching TA, synthesis helper, literature triage) without changing EZRA itself.

---

## Step-by-step: build and customize an agent

Follow these steps in order the first time. After that, iterate on the prompt and model list as your workflow changes.

### Step 1. Install EZRA and confirm the gallery

From the repo root:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate          # Linux / macOS / HPC

pip install -e .
ezra doctor
ezra models list
```

Fix anything `ezra doctor` flags (models directory, token, writable path) before downloading.

### Step 2. Decide: shareable or private

| Choice | Command | Git |
|--------|---------|-----|
| Share with the lab / open a PR | `ezra agents init my-lab-assistant` | Commit `agents/my-lab-assistant/` |
| Private experiment only | `ezra agents init local/scratch-bot` | Under `agents/local/` (gitignored) |

Use a short kebab-case name (`matsci-ta`, `synth-helper`). Do not start names with `_` (reserved for templates).

Optional description at create time:

```bash
ezra agents init teaching-ta --description "Office-hours helper for undergrad chem"
```

### Step 3. Scaffold the agent

```bash
ezra agents init my-lab-assistant
ezra agents list
```

EZRA copies `agents/_template/` to `agents/my-lab-assistant/` with three files:

| File | What you customize |
|------|--------------------|
| `agent.yaml` | Name, description, preferred / fallback models, tags, science focus |
| `prompt.md` | System prompt (role, style, boundaries) |
| `NOTES.md` | Human notes for you or your lab (hardware, owner, intent) |

Inspect what was created:

```bash
ezra agents show my-lab-assistant
ezra agents show my-lab-assistant --prompt
```

### Step 4. Pick models that fit this machine

Do not guess aliases. Probe hardware, then copy real gallery names into `agent.yaml`.

```bash
# keyword is optional but helps for science work
ezra models recommend
ezra models recommend chemistry
ezra models recommend materials --limit 5
ezra models recommend reasoning --format gguf
```

Note 1-3 strong fits for **preferred** and 1-2 smaller / safer fits for **fallback** (so the agent still works on a weaker laptop or when a large model is missing).

Useful discovery commands:

```bash
ezra models list --query chem
ezra models info chemllm-7b
ezra models list --science
```

### Step 5. Edit `agent.yaml`

Open `agents/my-lab-assistant/agent.yaml` and search for `CUSTOMIZE ME`. Set at least:

1. **`name` / `description`** - what this agent is for (one sentence).
2. **`models.preferred`** - gallery aliases from Step 4 (order matters: first is tried first later).
3. **`models.fallback`** - lighter aliases if preferred are missing or do not fit.
4. **`models.tags`** - optional hints such as `chemistry`, `materials`, `reasoning`.
5. **`science_focus`** - domain labels (`chemistry`, `materials`, `general`, ...).

Example shape (adapt aliases to what `recommend` returned on *your* machine):

```yaml
version: 1
name: my-lab-assistant
description: Materials lab Q&A helper for notebook and literature triage.

models:
  preferred:
    - chemllm-7b
    - qwen2.5-7b-instruct
  fallback:
    - phi-3.5-mini-instruct
    - gemma-2-2b-it
  tags:
    - chemistry
    - materials

prompt: prompt.md

science_focus:
  - chemistry
  - materials

tools: []
```

Tips:

- Only use aliases that appear in `ezra models list`. Typos fail `ezra agents check`.
- Keep preferred short (2-3). Long lists are harder to download and maintain.
- Match hardware: a 3B/7B GGUF on a laptop; larger science models on GPU / HPC nodes.
- Leave `tools: []` for now (reserved for later tool hooks).

Study the shipped example anytime:

```bash
ezra agents show chem-assistant
ezra agents show chem-assistant --prompt
```

Copy ideas into *your* agent; avoid editing `chem-assistant` in place if you pull upstream updates.

### Step 6. Write an effective `prompt.md`

Edit `agents/my-lab-assistant/prompt.md`. A strong prompt is short, structured, and specific.

Use this pattern:

1. **Role** - who the assistant is (domain + audience).
2. **Priorities** - what "good" means (units, safety, no invented citations).
3. **Typical tasks** - 3-6 jobs it should handle well.
4. **Style** - length, tone, when to ask clarifying questions.
5. **Boundaries** - what it must not do (secrets, fake papers, unsafe SOP claims).

Effective habits:

- Name the agent in the first line so transcripts stay clear.
- Separate experimental advice from computational / theoretical claims when relevant.
- Tell it to ask for missing context (solvent, temperature, scale) instead of assuming.
- Keep unpublished data and tokens out of tracked prompts; use `agents/local/` for private text.
- Prefer bullets and numbered priorities over a long essay.

Minimal starter:

```markdown
# System prompt - my-lab-assistant

You are **my-lab-assistant**, a research helper for materials and chemistry
running on open models via EZRA.

## Priorities

1. Be careful with units, stoichiometry, and significant figures.
2. Do not invent citations or experimental results.
3. Ask for missing experimental context before assuming.

## Style

Short answers first; offer a deeper dive. Use bullet lists for procedures.
```

### Step 7. Fill `NOTES.md` (for humans)

`NOTES.md` is for collaborators, not the model. Record:

- Owner / lab
- Intended use (notebook Q&A, teaching, literature triage)
- Hardware target (laptop / single GPU / HPC)
- Related `EZRA_SITE` if you submit jobs on a cluster

### Step 8. Validate the agent

```bash
ezra agents check my-lab-assistant
```

`check` confirms preferred / fallback aliases exist in the gallery and suggests downloads for anything missing. Fix YAML typos until check is clean.

Also re-read the assembled profile:

```bash
ezra agents show my-lab-assistant
ezra agents show my-lab-assistant --prompt
```

### Step 9. Download the models you pinned

```bash
# dry-run first if you want to see paths / files without downloading
ezra models download chemllm-7b qwen2.5-7b-instruct --dry-run

ezra models download chemllm-7b qwen2.5-7b-instruct
ezra models status
```

On HPC, set scratch / site profile first (see [HPC](hpc.md) and [sites](sites.md)):

```bash
export EZRA_SITE=my-cluster
ezra hpc submit download --dry-run
```

### Step 10. Iterate

Treat the agent as a living profile:

1. Change the prompt when answers are too vague, too long, or off-domain.
2. Swap preferred aliases when `ezra models recommend` finds a better fit.
3. Re-run `ezra agents check` after every YAML edit.
4. Keep a private fork under `agents/local/` while experimenting; promote to `agents/<name>/` when shareable.

---

## Commands reference

| Command | Description |
|---------|-------------|
| `ezra agents list` | Profiles under `agents/` (including `agents/local/...`) |
| `ezra agents init NAME` | Copy `agents/_template` to `agents/<NAME>` |
| `ezra agents show NAME` | Summary + prompt preview (`--prompt` for full text) |
| `ezra agents check NAME` | Validate aliases against the gallery; suggest downloads |

`init` flags: `--force`, `--description "..."`.

Names may be `my-bot` or `local/my-bot`.

---

## Agent folder layout

```text
agents/
  _template/          # copied by ezra agents init
  chem-assistant/     # shipped example (chemistry / materials)
  my-lab-assistant/   # yours
    agent.yaml
    prompt.md
    NOTES.md
  local/              # gitignored - private only
    scratch-bot/
```

### `agent.yaml` fields

| Field | Meaning |
|-------|---------|
| `name` / `description` | Display metadata |
| `models.preferred` | Gallery aliases tried first |
| `models.fallback` | Used if preferred are missing / unfit |
| `models.tags` | Optional gallery tag hints (`chemistry`, `materials`, ...) |
| `prompt` | Relative path to the system prompt (default `prompt.md`) |
| `science_focus` | Domain labels for docs / future routing |
| `tools` | Reserved for Phase 3 tool hooks (leave `[]` for now) |

---

## Worked example: chemistry helper

```bash
ezra agents init chem-helper --description "Lab chemistry Q&A"
ezra models recommend chemistry
# edit agents/chem-helper/agent.yaml  -> preferred/fallback from recommend
# edit agents/chem-helper/prompt.md   -> role, safety, no fake citations
ezra agents check chem-helper
ezra models download chemllm-7b qwen2.5-7b-instruct
ezra agents show chem-helper --prompt
```

Compare with the shipped starter:

```bash
ezra agents show chem-assistant --prompt
```

---

## Personal vs shareable

- **Shareable:** commit `agents/<name>/` (no tokens, no private lab data).
- **Private:** `ezra agents init local/my-bot` lives under `agents/local/` (gitignored).

When opening a PR with a new agent, include why it exists, which models it pins, and that `ezra agents check` passed. See [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Related

- [Models](models.md) - recommend / download
- [Conversation runtime](conversation.md) - planned sessions / chat / serve (how UIs will bind these agents)
- [Configuration](configuration.md) - `ezra.yaml`, env vars
- [CLI](cli.md) - full command list
- [agents/README.md](../agents/README.md) - short overview in-tree
- [HPC / SLURM](hpc.md) - download or serve on a cluster with a site profile
