"""Point Cline at EZRA's local OpenAI-compatible serve (no cloud API key).

Cline's default providers (Anthropic, OpenRouter, Cline account, …) need a
paid cloud key. EZRA already exposes downloaded gallery weights via
``ezra serve`` (``POST /v1/chat/completions``). Cline's
``openai-compatible`` provider can use that URL instead.

This module only **describes** the commands. It does not start ``ezra serve``
or a Cline agent session. ``ezra cline use-local --auth`` may save Cline's
provider settings when the user asks.
"""

from __future__ import annotations

import os
from typing import Any

PLACEHOLDER_API_KEY = "ezra-local"
DEFAULT_BIND_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def serve_base_url(host: str | None = None, port: int | None = None) -> str:
    """Client URL for ``ezra serve`` (never advertise ``0.0.0.0``)."""
    raw_host = (host or os.environ.get("EZRA_HOST") or DEFAULT_BIND_HOST).strip()
    if raw_host in {"0.0.0.0", "::", "[::]"}:
        raw_host = DEFAULT_BIND_HOST
    raw_port = port
    if raw_port is None:
        env_port = os.environ.get("EZRA_PORT", "").strip()
        raw_port = int(env_port) if env_port else DEFAULT_PORT
    return f"http://{raw_host}:{int(raw_port)}/v1"


def pick_installed_model(
    *,
    name: str | None = None,
    config: Any = None,
) -> str | None:
    """Return a gallery alias that is already on disk (prefer GGUF)."""
    from ezra.config import load_config
    from ezra.downloader import ModelDownloader
    from ezra.gallery import ModelGallery

    cfg = config if config is not None else load_config()
    gallery = ModelGallery()
    dl = ModelDownloader(cfg, gallery)
    if name:
        try:
            spec = gallery.get(name)
        except KeyError:
            return name.strip() or None
        return spec.name
    installed = dl.list_installed()
    if not installed:
        return None
    gguf = [s for s in installed if s.format.lower() == "gguf"]
    return (gguf[0] if gguf else installed[0]).name


def local_provider_plan(
    *,
    model: str | None = None,
    host: str | None = None,
    port: int | None = None,
    config: Any = None,
) -> dict[str, Any]:
    """Describe how to run Cline against ``ezra serve`` (no cloud key).

    ``api_key`` is a dummy string Cline's openai-compatible provider requires;
    EZRA serve does not authenticate it.
    """
    from ezra.config import load_config

    cfg = config if config is not None else load_config()
    chosen = pick_installed_model(name=model, config=cfg)
    base = serve_base_url(host, port)
    bind_host = DEFAULT_BIND_HOST
    bind_port = int(port or os.environ.get("EZRA_PORT") or DEFAULT_PORT)
    plan: dict[str, Any] = {
        "needs_cloud_key": False,
        "provider": "openai-compatible",
        "api_key": PLACEHOLDER_API_KEY,
        "base_url": base,
        "model": chosen,
        "serve_argv": (
            [
                "serve",
                "--model",
                chosen,
                "--host",
                bind_host,
                "--port",
                str(bind_port),
            ]
            if chosen
            else None
        ),
        "auth_argv": (
            [
                "auth",
                "--provider",
                "openai-compatible",
                "--apikey",
                PLACEHOLDER_API_KEY,
                "--modelid",
                chosen,
                "--baseurl",
                base,
            ]
            if chosen
            else None
        ),
        "run_flags": [
            "-P",
            "openai-compatible",
            "-k",
            PLACEHOLDER_API_KEY,
            *(["-m", chosen] if chosen else []),
        ],
        "note": (
            "Cline talks to ezra serve (your downloaded gallery weights). "
            "No Anthropic / OpenRouter / Cline-account key. "
            "Start serve, then ezra cline use-local --auth once."
        ),
    }
    if chosen is None:
        plan["hint"] = (
            "Download a GGUF first, e.g. "
            "ezra models download qwen2.5-7b-instruct"
        )
    return plan
