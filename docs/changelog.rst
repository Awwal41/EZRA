Changelog
=========

EZRA is in early development (``0.1.x``). Notable user-facing changes will be
listed here as releases land.

0.1.0
-----

* Curated free/open model gallery and Hugging Face downloads
* ``ezra models recommend`` - hardware-aware open-model picks (keyword + RAM/VRAM)
* Personal agent scaffolds (``ezra agents init`` / ``show`` / ``check``) under ``agents/``
* HPC site profiles and ``ezra hpc submit`` / SBATCH helpers
* Sphinx + MyST documentation site
* Conversation session API (``ezra.conversation``) with agent binding + stub backend
* Local inference (llama.cpp / MLX) and ``ezra chat`` / ``ezra serve`` (OpenAI ``/v1``)
* Document parsing module (``ezra.parse``) with vendored MegaParse + ``ezra parse`` / ``ezra chat --file``
* Peekaboo full in-tree snapshot (``third_party/Peekaboo``) + ``ezra.peekaboo`` (macOS MCP)
* gogcli full in-tree snapshot (``third_party/gogcli`` @ ``v0.35.0``) + ``ezra.gog``
* OpenClaw full in-tree snapshot (``third_party/OpenClaw`` @ ``v2026.6.34``) + ``ezra.openclaw`` (no auto-start)
* Cline full in-tree snapshot (``third_party/Cline`` @ ``afab68f3…``) + ``ezra.cline`` (no auto-start)
* Voicebox full in-tree snapshot (``third_party/Voicebox`` @ ``51f49dea…``) + ``ezra.voicebox`` (no auto-start)
* EZRA Grid VS Code / Cursor extension (``ide/vscode``) + ``ezra ide package|install`` (sideload only; no marketplace)
* Cline ``ezra cline use-local`` — openai-compatible provider on ``ezra serve`` (downloaded GGUFs; no cloud API key)
* Guide: Cline + a free gallery GGUF in VS Code / Cursor (``docs/cline-local.md``)
* Beginner walkthrough + llama.cpp wheel files (``docs/getting-started.md``, ``requirements-ide-*.txt``)
* MegaParse full in-tree library snapshot (``third_party/MegaParse``) + ``ezra.parse``
* Design note for chat / serve runtime (``docs/conversation.md``)
* Optional Vercel docs deploy (``vercel.json`` + ``.github/workflows/docs-vercel.yml``)
