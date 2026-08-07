# Agent notes - chem-assistant

Starter chemistry / materials agent shipped with EZRA. Adapt it:

```bash
ezra agents init my-chem-bot
# then copy ideas from agents/chem-assistant/{agent.yaml,prompt.md}
```

| Field | Notes |
|-------|--------|
| Intended use | Notebook Q&A, teaching, lit triage |
| Preferred models | `chemllm-7b`, `qwen2.5-7b-instruct` (see agent.yaml) |
| Hardware | Laptop-friendly fallbacks included; use `ezra models recommend chemistry` |

## Check & download

```bash
ezra agents check chem-assistant
ezra models recommend chemistry
ezra models download chemllm-7b
```
