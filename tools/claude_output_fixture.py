"""Independent AgentOutput fixture from claude-agent-sdk 0.3.284 sdk-tools.d.ts.

Source: https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk/v/0.3.284
Keep this consumer contract independent of the production redaction helper.
"""
from __future__ import annotations

import math


def completed_output(**changes):
    return {
        "status": "completed", "agentId": "advisor-a", "prompt": "PRIVATE_PROMPT",
        "content": [{"type": "text", "text": "PRIVATE_REPORT", "citations": ["PRIVATE_CITATION"]}],
        "totalToolUseCount": 3, "totalDurationMs": 125, "totalTokens": 42,
        "usage": {"input_tokens": 30, "output_tokens": 12, "cache_creation_input_tokens": None,
                  "cache_read_input_tokens": 0, "server_tool_use": None, "service_tier": "standard",
                  "cache_creation": None},
        **changes,
    }


def assert_agent_output(case, value):
    """Check required native fields, not equality to the producer's key set."""
    def strings(*keys):
        for key in keys:
            case.assertIsInstance(value[key], str, key)

    def number(value):
        case.assertIn(type(value), (int, float))
        case.assertTrue(math.isfinite(value))

    status = value["status"]
    case.assertIn(status, ("completed", "async_launched", "remote_launched"))
    strings("prompt")
    if status == "completed":
        strings("agentId")
        case.assertIsInstance(value["content"], list)
        for block in value["content"]:
            case.assertEqual(block["type"], "text")
            case.assertIsInstance(block["text"], str)
        for key in ("totalToolUseCount", "totalDurationMs", "totalTokens"):
            number(value[key])
        usage = value["usage"]
        for key in ("input_tokens", "output_tokens"):
            number(usage[key])
        for key in ("cache_creation_input_tokens", "cache_read_input_tokens"):
            if usage[key] is not None:
                number(usage[key])
        if usage["service_tier"] is not None:
            case.assertIsInstance(usage["service_tier"], str)
        for key, children in (
            ("server_tool_use", ("web_search_requests", "web_fetch_requests")),
            ("cache_creation", ("ephemeral_1h_input_tokens", "ephemeral_5m_input_tokens")),
        ):
            if usage[key] is not None:
                for child in children:
                    number(usage[key][child])
    elif status == "async_launched":
        strings("agentId", "description", "outputFile")
    else:
        strings("taskId", "sessionUrl", "description", "outputFile")
