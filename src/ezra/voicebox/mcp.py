"""Voicebox MCP / REST helpers (HTTP-first; optional stdio shim)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urljoin

from ezra.voicebox.paths import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    resolve_mcp_shim,
    voicebox_root,
)


class VoiceboxNotAvailable(RuntimeError):
    """Raised when Voicebox cannot be resolved or reached."""


def voicebox_available() -> bool:
    """True if the vendored tree is present (does not require a running app)."""
    return voicebox_root() is not None


def base_url(*, host: str | None = None, port: int | None = None) -> str:
    """Return the Voicebox HTTP base URL (default ``http://127.0.0.1:17493``)."""
    env_url = os.environ.get("EZRA_VOICEBOX_URL", "").strip()
    if env_url and host is None and port is None:
        return env_url.rstrip("/")
    h = (host or os.environ.get("VOICEBOX_HOST", "").strip() or DEFAULT_HOST).strip()
    if port is None:
        env_port = os.environ.get("VOICEBOX_PORT", "").strip()
        p = int(env_port) if env_port else DEFAULT_PORT
    else:
        p = port
    return f"http://{h}:{p}"


def mcp_url(*, host: str | None = None, port: int | None = None) -> str:
    """Return the Streamable HTTP MCP endpoint (``…/mcp``)."""
    return urljoin(base_url(host=host, port=port) + "/", "mcp")


def client_id(default: str = "ezra") -> str:
    """Client id stamped into ``X-Voicebox-Client-Id`` / ``VOICEBOX_CLIENT_ID``."""
    return (
        os.environ.get("EZRA_VOICEBOX_CLIENT_ID", "").strip()
        or os.environ.get("VOICEBOX_CLIENT_ID", "").strip()
        or default
    )


def mcp_http_config(*, client: str | None = None) -> dict[str, Any]:
    """Cursor / Claude-compatible MCP snippet for Voicebox HTTP transport."""
    cid = client or client_id()
    return {
        "mcpServers": {
            "voicebox": {
                "url": mcp_url(),
                "headers": {"X-Voicebox-Client-Id": cid},
            }
        }
    }


def mcp_stdio_command() -> list[str] | None:
    """Return argv for the stdio ``voicebox-mcp`` shim, or None if unresolved."""
    shim = resolve_mcp_shim()
    if shim is None:
        return None
    return [str(shim)]


def mcp_stdio_config(*, client: str | None = None) -> dict[str, Any] | None:
    """MCP snippet for stdio transport when a shim binary is available."""
    argv = mcp_stdio_command()
    if not argv:
        return None
    cid = client or client_id()
    return {
        "mcpServers": {
            "voicebox": {
                "command": argv[0],
                "args": argv[1:],
                "env": {"VOICEBOX_CLIENT_ID": cid},
            }
        }
    }


def probe_server(*, timeout: float = 2.0) -> dict[str, Any]:
    """Best-effort ``GET /health`` against a running Voicebox backend.

    Never starts the app. Returns a small status dict; ``ok`` is False when
    unreachable (no exception for the common offline case).
    """
    url = urljoin(base_url() + "/", "health")
    result: dict[str, Any] = {
        "url": url,
        "ok": False,
        "status_code": None,
        "body": None,
        "error": None,
    }
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            result["status_code"] = getattr(resp, "status", None) or resp.getcode()
            result["ok"] = 200 <= int(result["status_code"] or 0) < 300
            try:
                result["body"] = json.loads(body)
            except json.JSONDecodeError:
                result["body"] = body.strip() or None
    except urllib.error.HTTPError as exc:
        result["status_code"] = exc.code
        result["error"] = str(exc.reason or exc)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result["error"] = str(exc.reason if hasattr(exc, "reason") else exc)
    return result
