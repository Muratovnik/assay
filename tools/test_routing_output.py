"""Native output contracts and private-field boundaries, without inference."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/route-subagents/scripts"))
from route_evidence.claude_output import redact_agent_output
from routing_hook import failure
from claude_output_fixture import assert_agent_output, completed_output


class AgentOutputTests(unittest.TestCase):
    def test_completed_output_preserves_numeric_usage_but_no_nested_report_channels(self):
        raw = completed_output(resolvedModel="claude-sonnet", modelsUsed=["claude-sonnet"],
                               worktreePath="PRIVATE_PATH", worktreeBranch="PRIVATE_BRANCH",
                               summary="PRIVATE_SUMMARY", error={"text": "PRIVATE_ERROR"})
        raw["usage"].update(iterations={"text": "PRIVATE_ITERATION"}, service_tier="PRIVATE_TIER",
                            inference_geo="PRIVATE_GEO", output_tokens_details={"text": "PRIVATE_DETAIL"},
                            server_tool_use={"web_search_requests": 2, "web_fetch_requests": 1, "report": "PRIVATE_REPORT"},
                            cache_creation={"ephemeral_1h_input_tokens": 7, "ephemeral_5m_input_tokens": 9})
        before = copy.deepcopy(raw)
        safe = redact_agent_output(raw, "Read registered decision.")
        assert_agent_output(self, safe)
        self.assertNotIn("PRIVATE_", json.dumps(safe))
        self.assertEqual(before, raw)
        self.assertEqual(2, safe["usage"]["server_tool_use"]["web_search_requests"])
        self.assertEqual(9, safe["usage"]["cache_creation"]["ephemeral_5m_input_tokens"])
        self.assertEqual("claude-sonnet", safe["resolvedModel"])
        self.assertEqual(42, safe["totalTokens"])

    def test_async_and_remote_envelopes_suppress_report_and_artifact_paths(self):
        for status in ("async_launched", "remote_launched"):
            with self.subTest(status=status):
                raw = {"status": status, "agentId": "advisor-a", "taskId": "task-a",
                       "prompt": "PRIVATE_PROMPT", "description": "PRIVATE_REPORT",
                       "outputFile": "PRIVATE_PATH", "sessionUrl": "PRIVATE_URL"}
                safe = redact_agent_output(raw, "Read registered decision.")
                assert_agent_output(self, safe)
                self.assertEqual(status, safe["status"])
                self.assertNotIn("PRIVATE_", json.dumps(safe))
                self.assertEqual("", safe["outputFile"])
                self.assertIn("Read registered decision.", safe["description"])

    def test_guard_failure_also_returns_a_valid_native_envelope(self):
        for raw in (completed_output(), {"status": "async_launched"}, {"status": "remote_launched"},
                    {"status": "future", "report": "PRIVATE_REPORT"}, "PRIVATE_REPORT", None):
            with self.subTest(raw=type(raw)):
                reply = failure({"hook_event_name": "PostToolUse", "tool_name": "Agent",
                                 "tool_response": raw}, "plugin", True)
                safe = reply["hookSpecificOutput"]["updatedToolOutput"]
                assert_agent_output(self, safe)
                self.assertNotIn("PRIVATE_", json.dumps(safe))
                self.assertIn("could not validate", json.dumps(safe))

    def test_malformed_telemetry_cannot_inject_text_or_non_json_numbers(self):
        for bad in (True, -1, 10**30, float("inf"), float("nan"), "PRIVATE_REPORT", {}):
            with self.subTest(bad=bad):
                raw = completed_output(totalTokens=bad, resolvedModel={"text": "PRIVATE_REPORT"},
                                       modelsUsed=["invalid model PRIVATE_REPORT"])
                raw["usage"]["input_tokens"] = bad
                safe = redact_agent_output(raw, "Read registered decision.")
                assert_agent_output(self, safe)
                self.assertNotIn("PRIVATE_", json.dumps(safe, allow_nan=False))
                self.assertEqual(0, safe["totalTokens"])

    def test_contract_rejects_the_former_incomplete_replacement(self):
        with self.assertRaises((AssertionError, KeyError)):
            assert_agent_output(self, {"agentId": "advisor-a", "status": "completed", "content": []})


if __name__ == "__main__":
    unittest.main()
