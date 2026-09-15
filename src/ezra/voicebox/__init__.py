"""Voicebox integration — local AI voice studio for EZRA agents.

Upstream is a **full in-tree snapshot** at ``third_party/Voicebox/``
([jamiepine/voicebox](https://github.com/jamiepine/voicebox), MIT).

Voicebox runs a local FastAPI backend (default port ``17493``) with a built-in
MCP server at ``/mcp`` (``voicebox.speak``, transcribe, profiles, captures).
Prefer this package over calling the vendor tree directly.

EZRA never auto-starts the Voicebox app or downloads TTS/STT models.

Typical usage::

    from ezra.voicebox import voicebox_available, mcp_http_config, probe_server

    if voicebox_available():
        print(mcp_http_config())   # paste into Cursor MCP settings
        print(probe_server())      # only if the app is already running
"""

from __future__ import annotations

from ezra.voicebox.mcp import (
    VoiceboxNotAvailable,
    base_url,
    client_id,
    mcp_http_config,
    mcp_stdio_command,
    mcp_stdio_config,
    mcp_url,
    probe_server,
    voicebox_available,
)
from ezra.voicebox.paths import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    resolve_mcp_shim,
    voicebox_pin_info,
    voicebox_root,
)

__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "VoiceboxNotAvailable",
    "base_url",
    "client_id",
    "mcp_http_config",
    "mcp_stdio_command",
    "mcp_stdio_config",
    "mcp_url",
    "probe_server",
    "resolve_mcp_shim",
    "voicebox_available",
    "voicebox_pin_info",
    "voicebox_root",
]
