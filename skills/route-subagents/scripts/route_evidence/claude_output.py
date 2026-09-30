"""Redact Claude Agent returns without breaking its native output union.

Claude ignores a replacement that fails AgentOutput validation. Required fields
below follow claude-agent-sdk 0.3.284 sdk-tools.d.ts; arbitrary nested strings,
citations, prompts and output paths are never copied as routing evidence.
"""
from __future__ import annotations

import math
import re

TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}\Z")


def _token(value):
    return value if isinstance(value, str) and TOKEN.fullmatch(value) else None


def _number(value):
    return value if type(value) in (int, float) and 0 <= value < 10**15 and math.isfinite(value) else 0


def _usage(raw):
    raw = raw if isinstance(raw, dict) else {}
    value = {key: _number(raw.get(key)) for key in ("input_tokens", "output_tokens")}
    for key in ("cache_creation_input_tokens", "cache_read_input_tokens"):
        value[key] = None if raw.get(key) is None else _number(raw[key])
    for key, fields in (
        ("server_tool_use", ("web_search_requests", "web_fetch_requests")),
        ("cache_creation", ("ephemeral_1h_input_tokens", "ephemeral_5m_input_tokens")),
    ):
        nested = raw.get(key)
        value[key] = {field: _number(nested.get(field)) for field in fields} if isinstance(nested, dict) else None
    value["service_tier"] = None
    return value


def redact_agent_output(response, message):
    """Build a schema-valid replacement, including on guard failure.

    A missing/unknown envelope becomes a completed *tool return* with an
    unverified identity and neutral telemetry, not evidence of agent success.
    The caller records host observations separately before redaction.
    """
    raw = response if isinstance(response, dict) else {}
    status = raw.get("status")
    if status not in ("completed", "async_launched", "remote_launched"):
        message = "Unverified agent return; telemetry unavailable. " + message
        raw, status = {}, "completed"
    safe = {"status": status, "prompt": ""}
    if status == "remote_launched":
        safe.update(taskId=_token(raw.get("taskId")) or "unverified",
                    sessionUrl="", description=message, outputFile="")
        return safe
    safe["agentId"] = _token(raw.get("agentId")) or "unverified"
    model = _token(raw.get("resolvedModel"))
    if model:
        safe["resolvedModel"] = model
    used = raw.get("modelsUsed")
    if isinstance(used, list) and len(used) <= 16 and all(_token(item) for item in used):
        safe["modelsUsed"] = list(used)
    if status == "async_launched":
        safe.update(description=message, outputFile="", canReadOutputFile=False)
    else:
        safe["content"] = [{"type": "text", "text": message}]
        for key in ("totalDurationMs", "totalTokens", "totalToolUseCount"):
            safe[key] = _number(raw.get(key))
        safe["usage"] = _usage(raw.get("usage"))
    return safe
