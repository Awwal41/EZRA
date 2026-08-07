# Agent notes - CUSTOMIZE ME

Personal agent scaffolded with `ezra agents init`. Edit `agent.yaml` and
`prompt.md`, then keep this folder private (`agents/local/`) or commit it if
you want to share a lab-ready agent.

| Field | Your notes |
|-------|------------|
| Owner / lab | |
| Intended use | e.g. notebook Q&A, synthesis planning, literature triage |
| Preferred models | gallery aliases in `agent.yaml` |
| Hardware target | laptop / single GPU / HPC |
| Related site profile | `EZRA_SITE=...` if any |

## Quick start

```bash
ezra agents show <this-folder-name>
ezra agents check <this-folder-name>
ezra models recommend              # pick something that fits this machine
# edit models.preferred in agent.yaml to match, then:
ezra models download <preferred-alias>
```

## Sharing (optional)

```bash
git add agents/<this-folder-name>
git commit -m "Add <name> personal agent profile"
git push
```

Do not commit tokens, private data, or unpublished results in `prompt.md`.
