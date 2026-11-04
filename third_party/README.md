# Third-party integrations

EZRA integrates with the open-source projects below. Their source trees are
**not stored in this repository** — download them at the pinned versions EZRA
is built against:

```bash
python scripts/fetch_third_party.py              # all vendors
python scripts/fetch_third_party.py Cline        # just one
python scripts/fetch_third_party.py --list       # show pins
```

Each tree lands in `third_party/<Name>/` with an `UPSTREAM.txt` recording the
source and pin. This folder is git-ignored apart from this README.

| Path | Upstream | License | EZRA adapter |
|------|----------|---------|--------------|
| `OpenClaw/` | [openclaw/openclaw](https://github.com/openclaw/openclaw) | MIT | [`ezra.openclaw`](../src/ezra/openclaw/) |
| `Peekaboo/` | [openclaw/Peekaboo](https://github.com/openclaw/Peekaboo) | MIT | [`ezra.peekaboo`](../src/ezra/peekaboo/) |
| `gogcli/` | [openclaw/gogcli](https://github.com/openclaw/gogcli) | MIT | [`ezra.gog`](../src/ezra/gog/) |
| `MegaParse/` | [QuivrHQ/MegaParse](https://github.com/QuivrHQ/MegaParse) | Apache-2.0 | [`ezra.parse`](../src/ezra/parse/) |
| `Cline/` | [cline/cline](https://github.com/cline/cline) | Apache-2.0 | [`ezra.cline`](../src/ezra/cline/) |
| `Voicebox/` | [jamiepine/voicebox](https://github.com/jamiepine/voicebox) | MIT | [`ezra.voicebox`](../src/ezra/voicebox/) |

EZRA works without these trees; the matching `ezra <vendor> status` commands
report the integration as unavailable until it is fetched. If you keep a
checkout elsewhere, point EZRA at it with `EZRA_OPENCLAW_ROOT`,
`EZRA_PEEKABOO_ROOT`, `EZRA_GOG_ROOT`, `EZRA_CLINE_ROOT`, or
`EZRA_VOICEBOX_ROOT`.

## Rules

1. Import through the `ezra.*` adapters, not directly from these folders.
2. Change a pin deliberately in `scripts/fetch_third_party.py` and re-run with `--force`.
3. **No auto-start** — do not run OpenClaw onboard / Gateway, Cline agents, or Voicebox unless the user asks.
4. Upstream `LICENSE` / notices stay with each tree.
