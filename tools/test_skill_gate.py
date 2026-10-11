"""Claude skill gate: a reply that names an unloaded skill continues once; no model runs."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import skill_gate
from runtime.cli import process

NAMES = {"evidence-research", "code-change", "test-writing"}


class SkillGateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.now = 1000.0
        self.base = {"session_id": "session", "cwd": "work"}

    def apply(self, event, client="claude", directory=None):
        return skill_gate.apply({**self.base, **event}, client, NAMES,
                                self.directory if directory is None else directory, clock=lambda: self.now)

    def stop(self, text, **extra):
        return self.apply({"hook_event_name": "Stop", "last_assistant_message": text, **extra})

    def load(self, tool, data, **extra):
        return self.apply({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": data, **extra})

    def feedback(self, result):
        """The continuation text, once it is checked to be Stop feedback rather than a block."""
        self.assertNotIn("decision", result)
        output = result["hookSpecificOutput"]
        self.assertEqual({"hookEventName", "additionalContext"}, set(output))
        self.assertEqual("Stop", output["hookEventName"])
        return output["additionalContext"]

    def test_named_but_unloaded_skill_continues_the_turn_once(self):
        text = self.feedback(self.stop("Assay: evidence-research\n\nFrom memory: use /usage."))
        self.assertIn("names evidence-research", text)
        self.assertIn("has not loaded", text)
        self.assertEqual({}, self.stop("Assay: evidence-research\n\nStill unloaded.", stop_hook_active=True))

    def test_skill_tool_or_skill_file_read_satisfies_the_gate(self):
        self.assertEqual({}, self.load("Skill", {"skill": "assay:evidence-research"}))
        self.assertEqual({}, self.stop("Assay: evidence-research"))
        self.load("Read", {"file_path": "C:\\plugins\\assay\\skills\\code-change\\SKILL.md"})
        self.assertEqual({}, self.stop("**Assay:** code-change, evidence-research (already loaded)"))

    def test_only_the_missing_skill_is_named_in_the_reason(self):
        self.load("Skill", {"skill": "code-change"})
        text = self.feedback(self.stop("Assay: code-change, test-writing"))
        self.assertIn("test-writing", text)
        self.assertNotIn("code-change", text)

    def test_none_unknown_names_and_replies_without_a_leading_line_pass(self):
        for text in ("Assay: none", "Assay: none. Nothing here needs a method.", "Assay: plugin-authoring",
                     "Just the answer.", "", None, "Intro first.\nAssay: code-change"):
            with self.subTest(text=text):
                self.assertEqual({}, self.stop(text))

    def test_other_tools_and_other_skills_are_not_loads(self):
        self.load("Skill", {"skill": "plugin-authoring"})
        self.load("Read", {"file_path": "/plugins/assay/skills/code-change/references/reuse.md"})
        self.load("Grep", {"pattern": "skills/code-change/SKILL.md"})
        self.assertIn("code-change", self.feedback(self.stop("Assay: code-change")))

    def test_a_subagent_or_another_session_cannot_satisfy_the_root(self):
        self.load("Skill", {"skill": "evidence-research"}, agent_id="worker")
        self.assertIn("evidence-research", self.feedback(self.stop("Assay: evidence-research")))
        self.load("Skill", {"skill": "evidence-research"}, session_id="other")
        self.assertIn("evidence-research", self.feedback(self.stop("Assay: evidence-research")))

    def test_loads_expire_with_their_record(self):
        self.load("Skill", {"skill": "code-change"})
        self.now += skill_gate.TTL + 1
        self.assertIn("code-change", self.feedback(self.stop("Assay: code-change")))

    def test_codex_missing_identity_and_missing_state_are_inert(self):
        stop = {"hook_event_name": "Stop", "last_assistant_message": "Assay: code-change"}
        self.assertEqual({}, self.apply(stop, client="codex"))
        self.assertEqual({}, self.apply({**stop, "session_id": None}))
        self.assertEqual({}, self.apply(stop, directory=""))

    def test_runtime_continues_claude_stops_and_honours_the_setting(self):
        environment = {"CLAUDE_PLUGIN_DATA": str(self.directory / "data")}
        stop = {"hook_event_name": "Stop", "session_id": "session", "cwd": "work",
                "last_assistant_message": "Assay: code-change\n\nDone."}
        result, error = process(stop, "claude", environment, clock=lambda: self.now)
        self.assertIsNone(error)
        self.assertIn("code-change", self.feedback(result))
        process({"hook_event_name": "PreToolUse", "session_id": "session", "cwd": "work", "tool_name": "Skill",
                 "tool_input": {"skill": "assay:code-change"}}, "claude", environment, clock=lambda: self.now)
        self.assertEqual({}, process(stop, "claude", environment, clock=lambda: self.now)[0])
        unloaded = {**stop, "last_assistant_message": "Assay: test-writing"}
        self.assertEqual({}, process(unloaded, "codex", environment, clock=lambda: self.now)[0])
        settings = self.directory / "settings.json"
        settings.write_text(json.dumps({"disabled_rules": ["skill-gate"]}), encoding="utf-8")
        result, _ = process(unloaded, "claude", {**environment, "ASSAY_HOOK_CONFIG": str(settings)},
                            clock=lambda: self.now)
        self.assertEqual({}, result)

    def test_only_the_claude_manifest_registers_stop(self):
        claude = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
        codex = json.loads((ROOT / "hooks/codex.json").read_text(encoding="utf-8"))["hooks"]
        self.assertIn("Stop", claude)
        self.assertNotIn("Stop", codex)


if __name__ == "__main__":
    unittest.main()
