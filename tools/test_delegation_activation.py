"""Offline hint contracts; these checks do not exercise model delegation."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


activation = load_module("delegation_activation", ROOT / "hooks/runtime/activation.py")
reminders = load_module("delegation_reminders", ROOT / "skills/route-subagents/scripts/skill_reminder.py")


class DelegationActivationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "hooks").mkdir()
        for path in ("catalog.toml", "hooks/activation-rules.toml"):
            shutil.copyfile(ROOT / path, self.root / path)
        catalog = tomllib.loads((self.root / "catalog.toml").read_text(encoding="utf-8"))
        # Simulate installed entries using the real catalog and rules. Content
        # is immaterial to selection; discovery in a native client is not tested.
        for asset in catalog["assets"]:
            if asset["kind"] == "skill":
                target = self.root / asset["path"] / "SKILL.md"
                target.parent.mkdir(parents=True)
                target.write_text("Fixture for " + asset["id"] + "\n", encoding="utf-8")
        self.rules, self.fingerprint = activation.load_rules(self.root)

    def decide(self, prompt, rules=None):
        return activation.evaluate(
            {"hook_event_name": "UserPromptSubmit", "prompt": prompt},
            self.rules if rules is None else rules,
        )

    def test_request_fixtures_and_existing_explicit_selection_contract(self):
        cases = json.loads((ROOT / "tools/fixtures/hooks/prompts.json").read_text(encoding="utf-8"))
        self.assertTrue(cases)
        for case in cases:
            with self.subTest(prompt=case["prompt"]):
                result = self.decide(case["prompt"])
                self.assertEqual(case["rules"], result["rule_ids"])
                self.assertLessEqual(len(result["rule_ids"]), 2)
                self.assertLessEqual(len(result["context"]), activation.MAX_CONTEXT)

    def test_disabled_rule_or_skill_preserves_the_primary_workflow(self):
        for options in ({"disabled_rules": ["delegation"]},
                        {"disabled_skills": ["skill/route-subagents"]}):
            with self.subTest(options=options):
                rules, fingerprint = activation.load_rules(self.root, **options)
                self.assertNotEqual(self.fingerprint, fingerprint)
                self.assertEqual(["research"], self.decide("Research alternatives with subagents", rules)["rule_ids"])
                self.assertEqual([], self.decide("Use subagents", rules)["rule_ids"])
                self.assertEqual([], self.decide("$route-subagents", rules)["rule_ids"])

    def test_missing_optional_skill_never_produces_a_delegation_hint(self):
        (self.root / "skills/route-subagents/SKILL.md").unlink()
        rules, _ = activation.load_rules(self.root)
        self.assertEqual(["planning"], self.decide("Create a plan; use subagents", rules)["rule_ids"])
        self.assertEqual([], self.decide("Use subagents", rules)["rule_ids"])

    def test_early_context_is_english_bounded_and_not_authorization(self):
        event = {"hook_event_name": "UserPromptSubmit", "prompt": "Используй субагентов для SECRET_SENTINEL"}
        original = copy.deepcopy(event)
        result = activation.evaluate(event, self.rules)
        self.assertEqual(original, event)
        self.assertEqual({"rule_ids", "context"}, set(result))
        self.assertEqual(["delegation"], result["rule_ids"])
        text = result["context"]
        self.assertIn("before substantial solo work", text)
        self.assertIn("already-authorized", text)
        self.assertIn("read-only", text)
        self.assertIn("not", text)
        self.assertNotIn("SECRET_SENTINEL", text)
        self.assertFalse(any("\u0400" <= character <= "\u04ff" for character in text))
        self.assertLessEqual(len(text), activation.MAX_CONTEXT)

    def test_restore_preserves_relevance_check_not_authority(self):
        text = activation.context(["research", "delegation"], self.rules, restored=True)
        self.assertIn("Previous request", text)
        self.assertIn("Recheck relevance", text)
        self.assertIn("already-authorized", text)
        self.assertLessEqual(len(text), activation.MAX_CONTEXT)

    def test_delegation_does_not_select_all_downstream_workflows(self):
        result = self.decide("Research alternatives using subagents; implement the result; review it")
        self.assertEqual(["research", "delegation"], result["rule_ids"])

    def test_non_prompt_events_do_not_create_new_intent(self):
        for name in ("PreToolUse", "PostToolUse", "SessionStart", "PostCompact"):
            with self.subTest(name=name):
                result = activation.evaluate({"hook_event_name": name, "prompt": "Use subagents"}, self.rules)
                self.assertEqual({"rule_ids": [], "context": ""}, result)

    def test_modified_method_invalidates_the_fingerprint(self):
        path = self.root / "skills/route-subagents/SKILL.md"
        path.write_text(path.read_text(encoding="utf-8") + "Changed procedure\n", encoding="utf-8")
        self.assertNotEqual(self.fingerprint, activation.load_rules(self.root)[1])


class DelegationReminderTests(unittest.TestCase):
    def test_session_reminder_reaches_planning_before_launch(self):
        for source in ("startup", "resume", "clear", "compact", "fork"):
            with self.subTest(source=source):
                result = reminders.reminder({"hook_event_name": "SessionStart", "source": source}, {})
                output = result["hookSpecificOutput"]
                self.assertEqual({"hookEventName", "additionalContext"}, set(output))
                self.assertIn("before substantial solo work", output["additionalContext"])
                self.assertIn("does not authorize delegation", output["additionalContext"])
                self.assertIn("workers must not spawn", output["additionalContext"])
                self.assertLessEqual(len(output["additionalContext"]), 1200)

    def test_required_claude_guard_still_owns_launches(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "routing.json"
            path.write_text(json.dumps({"schema_version": 3, "client": "claude", "pipeline": {"mode": "required"}}))
            environment = {"ASSAY_ROUTING_CONFIG": str(path)}
            for tool in ("Agent", "Task"):
                self.assertEqual({}, reminders.reminder({"hook_event_name": "PreToolUse", "tool_name": tool}, environment))
            result = reminders.reminder({"hook_event_name": "PreToolUse", "tool_name": "spawn_agent"}, environment)
            self.assertEqual({"hookEventName", "additionalContext"}, set(result["hookSpecificOutput"]))

    def test_no_launch_or_settings_mutation(self):
        event = {"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": {"prompt": "SECRET"}}
        before = copy.deepcopy(event)
        result = reminders.reminder(event, {})
        self.assertEqual(before, event)
        self.assertNotIn("SECRET", json.dumps(result))
        self.assertEqual({"hookEventName", "additionalContext"}, set(result["hookSpecificOutput"]))
        self.assertEqual({}, reminders.reminder({"hook_event_name": "PreToolUse", "tool_name": "read_file"}, {}))


if __name__ == "__main__":
    unittest.main()
