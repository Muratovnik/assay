"""Claude hand-back hold: a subagent's report meets the stop checks before it is delivered; no model runs."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import activation, handback
from runtime.cli import process

APP = "C:\\work\\src\\parser.py"
UPDATED = "The file {} has been updated successfully."
REPORT = "Fixed the parser so empty input returns an empty list."
VERIFIED = REPORT + "\nVerified: unit suite — local venv — after the parser fix"


def tool(name, data, ident):
    return {"type": "assistant", "isSidechain": True,
            "message": {"content": [{"type": "tool_use", "id": ident, "name": name, "input": data}]}}


def returned(ident, text="ok", error=False):
    return {"type": "user", "isSidechain": True, "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": ident, "content": text, **({"is_error": True} if error else {})}]}}


def packet(text="Fix the parser and report through your tools."):
    return {"type": "user", "isSidechain": True, "message": {"role": "user", "content": text}}


def edited():
    return [tool("Edit", {"file_path": APP, "old_string": "a", "new_string": "b"}, "e1"), returned("e1", UPDATED.format(APP))]


class HoldTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.data = self.directory / "data"
        self.session = self.directory / "s1.jsonl"
        self.session.write_text("", encoding="utf-8")

    def worker(self, *entries):
        """The subagent's own transcript, where Claude Code keeps it beside the session's."""
        path = self.directory / "s1" / "subagents" / "agent-a1.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        flat = [item for entry in entries for item in (entry if isinstance(entry, list) else [entry])]
        path.write_text("".join(json.dumps(entry) + "\n" for entry in flat), encoding="utf-8")
        return str(path)

    def handing_back(self, message=REPORT, prompt="p1", **extra):
        # The shape a live Claude Code 2.1.304 subagent sent: no agent_transcript_path, the session's transcript_path.
        return {"session_id": "s1", "hook_event_name": "PreToolUse", "tool_name": "SubagentHandback",
                "tool_input": {"message": message}, "agent_id": "a1", "agent_type": "general-purpose",
                "prompt_id": prompt, "transcript_path": str(self.session), **extra}

    def stopping(self, last="Done."):
        return {"session_id": "s1", "hook_event_name": "SubagentStop", "agent_id": "a1",
                "agent_type": "general-purpose", "last_assistant_message": last,
                "agent_transcript_path": str(self.directory / "s1" / "subagents" / "agent-a1.jsonl")}

    def run_hook(self, event, client="claude", **environment):
        result, error = process(event, client, {"CLAUDE_PLUGIN_DATA": str(self.data), **environment})
        self.assertIsNone(error)
        return result

    def test_the_first_hand_back_the_stop_checks_object_to_is_refused_and_the_retry_passes(self):
        self.worker(packet(), *edited())
        result = self.run_hook(self.handing_back())["hookSpecificOutput"]
        self.assertEqual("deny", result["permissionDecision"])
        reason = result["permissionDecisionReason"]
        self.assertTrue(reason.startswith("Assay held this hand-back once, so the report has not reached the parent"))
        self.assertIn("Assay report check", reason)
        self.assertIn("this turn edited parser.py", reason)
        # The check's own advice is for a delivered answer; the report must go out whole.
        self.assertIn("its advice not to repeat the answer does not apply here", reason)
        self.assertIn("call SubagentHandback again with the complete report, not only the added lines", reason)
        self.assertIn("That call goes through.", reason)
        # The retry is never refused, even when the report still lacks the line.
        self.assertEqual({}, self.run_hook(self.handing_back()))
        # A new request of the same subagent gets its own check.
        self.assertEqual("deny", self.run_hook(self.handing_back(prompt="p2"))["hookSpecificOutput"]["permissionDecision"])

    def test_a_report_that_carries_the_line_passes_at_once(self):
        self.worker(packet(), *edited())
        self.assertEqual({}, self.run_hook(self.handing_back(VERIFIED)))

    def test_an_announced_skill_the_subagent_did_not_load_is_held_by_the_gate(self):
        self.worker(packet(), tool("Read", {"file_path": APP}, "r1"), returned("r1"))
        reason = self.run_hook(self.handing_back("Used `assay:code-change` to review the parser.\nAll good."))[
            "hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Assay skill gate: this turn announces code-change", reason)
        loaded = [packet(), tool("Skill", {"skill": "assay:code-change"}, "k1"), returned("k1")]
        self.worker(*loaded)
        self.assertEqual({}, self.run_hook(self.handing_back("Used `assay:code-change`.\nAll good.", prompt="p3")))

    def test_nothing_is_refused_without_a_place_for_the_key_or_with_the_rule_off(self):
        self.worker(packet(), *edited())
        event = self.handing_back()
        # Without the data directory a refusal could repeat and lose the report.
        self.assertEqual(({}, None), process(event, "claude", {}))
        config = self.directory / "hooks.json"
        config.write_text(json.dumps({"disabled_rules": ["handback-hold"], "state_dir": str(self.data)}), encoding="utf-8")
        self.assertEqual(({}, None), process(event, "claude", {"ASSAY_HOOK_CONFIG": str(config)}))
        self.assertEqual({}, self.run_hook(event, client="codex"))
        # The main session does not hand back; a call without a report is not checked.
        self.assertEqual({}, self.run_hook({**event, "agent_id": None}))
        self.assertEqual({}, self.run_hook({**event, "tool_input": {}}))

    def test_after_a_delivered_hand_back_the_stop_stays_silent(self):
        self.worker(packet(), *edited(), tool("SubagentHandback", {"message": REPORT}, "h1"), returned("h1", "Delivered."))
        self.assertEqual({}, self.run_hook(self.stopping()))

    def test_after_a_refused_hand_back_the_stop_still_speaks(self):
        self.worker(packet(), *edited(), tool("SubagentHandback", {"message": REPORT}, "h1"),
                    returned("h1", "Assay held this hand-back once", error=True))
        text = self.run_hook(self.stopping())["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Assay report check", text)
        # So does a subagent that has not handed back, as before.
        self.worker(packet(), *edited())
        self.assertIn("Assay report check", self.run_hook(self.stopping())["hookSpecificOutput"]["additionalContext"])
        # A hand-back in an earlier turn of the same subagent does not silence this one.
        self.worker(packet(), tool("SubagentHandback", {"message": REPORT}, "h0"), returned("h0", "Delivered."),
                    packet("One more fix, please."), *edited())
        self.assertIn("Assay report check", self.run_hook(self.stopping())["hookSpecificOutput"]["additionalContext"])

    def test_the_rule_and_the_manifest(self):
        self.assertTrue(activation.load_rules(ROOT)[0].handback_hold)
        self.assertFalse(activation.load_rules(ROOT, disabled_rules=["handback-hold"])[0].handback_hold)
        groups = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
        own = [group for group in groups if group["matcher"] == "^SubagentHandback$"]
        self.assertEqual(15, own[0]["hooks"][0]["timeout"])
        self.assertNotIn("onFailure", own[0]["hooks"][0])
        # Exactly one group answers a hand-back.
        import re
        self.assertEqual(1, sum(bool(re.search(group["matcher"], "SubagentHandback")) for group in groups))
        self.assertFalse(handback.handing_back({"hook_event_name": "PreToolUse", "tool_name": "Read", "agent_id": "a1",
                                                "tool_input": {"message": "x"}}))


if __name__ == "__main__":
    unittest.main()
