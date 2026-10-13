"""Poseidon chat loop: local Ollama model + ClimateWise observation tools."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from services.poseidon_tools import OLLAMA_TOOLS, execute_tool

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("POSEIDON_MODEL", "poseidon")
DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
MAX_TOOL_ROUNDS = 6


def _parse_arguments(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _ollama_post(path: str, payload: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
    data = json.dumps(payload).encode()
    req = Request(
        f"{DEFAULT_HOST}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode() or "{}")


def _ollama_get(path: str, timeout: int = 8) -> Dict[str, Any]:
    req = Request(f"{DEFAULT_HOST}{path}", headers={"Accept": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode() or "{}")


def poseidon_status() -> Dict[str, Any]:
    try:
        tags = _ollama_get("/api/tags")
        names = [item.get("name") for item in tags.get("models") or []]
        present = any(
            (name or "").split(":")[0] == DEFAULT_MODEL.split(":")[0] for name in names
        )
        return {
            "ollama": True,
            "host": DEFAULT_HOST,
            "model": DEFAULT_MODEL,
            "model_present": present,
            "models": names,
        }
    except (URLError, HTTPError, TimeoutError, OSError) as exc:
        return {
            "ollama": False,
            "host": DEFAULT_HOST,
            "model": DEFAULT_MODEL,
            "model_present": False,
            "error": str(exc),
        }


async def chat(
    messages: List[Dict[str, str]],
    *,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    if not messages:
        raise ValueError("messages vazio")
    model_name = model or DEFAULT_MODEL
    transcript: List[Dict[str, Any]] = list(messages)
    trace: List[Dict[str, Any]] = []

    for _round in range(MAX_TOOL_ROUNDS):
        try:
            body = _ollama_post(
                "/api/chat",
                {
                    "model": model_name,
                    "messages": transcript,
                    "tools": OLLAMA_TOOLS,
                    "stream": False,
                    "think": False,
                    "options": {"temperature": 0.3},
                },
            )
        except HTTPError as exc:
            detail = exc.read().decode()[:400]
            raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(
                f"Ollama indisponível em {DEFAULT_HOST}. Suba o daemon e `ollama run {model_name}`."
            ) from exc

        msg = body.get("message") or {}
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            return {
                "reply": (msg.get("content") or "").strip(),
                "model": model_name,
                "tool_trace": trace,
                "rounds": _round + 1,
            }

        transcript.append(msg)
        for call in tool_calls:
            fn = (call.get("function") or {}) if isinstance(call, dict) else {}
            name = fn.get("name") or "unknown"
            arguments = _parse_arguments(fn.get("arguments"))
            result = await execute_tool(name, arguments)
            trace.append(
                {
                    "tool": name,
                    "arguments": arguments,
                    "status": (result.get("meta") or {}).get("status"),
                    "source": (result.get("meta") or {}).get("source"),
                }
            )
            transcript.append(
                {
                    "role": "tool",
                    "tool_name": name,
                    "content": json.dumps(result, default=str, ensure_ascii=False),
                }
            )

    return {
        "reply": "Limite de ferramentas atingido. Use os resultados já obtidos ou reformule a pergunta.",
        "model": model_name,
        "tool_trace": trace,
        "rounds": MAX_TOOL_ROUNDS,
    }
