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
* Peekaboo submodule (``third_party/Peekaboo``) + ``ezra.peekaboo`` / ``ezra peekaboo`` (macOS MCP)
* gogcli submodule (``third_party/gogcli``) + ``ezra.gog`` / ``ezra gog`` (Google Workspace MCP)
* OpenClaw submodule (``third_party/OpenClaw`` @ ``v2026.6.34``, shallow) + ``ezra.openclaw`` (no auto-start)
* Design note for chat / serve runtime (``docs/conversation.md``)
