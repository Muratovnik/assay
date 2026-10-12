"""Offline skill-check and reminder contracts; no model delegation is exercised."""
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


class SkillCheckActivationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "hooks").mkdir()
        for path in ("catalog.toml", "hooks/activation-rules.toml"):
            shutil.copyfile(ROOT / path, self.root / path)
        catalog = tomllib.loads((self.root / "catalog.toml").read_text(encoding="utf-8"))
        self.skills = [asset["id"] for asset in catalog["assets"] if asset["kind"] == "skill"]
        # Simulate installed entries using the real catalog and skill map.
        # Content is immaterial to the check; native discovery is not tested.
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

    def listed(self, text):
        section = text.split("Skills: ", 1)[1].rstrip(".")
        return [entry.split(" - ", 1)[0] for entry in section.split("; ")]

    def write_map(self, transform):
        path = self.root / "hooks/activation-rules.toml"
        path.write_text(transform(path.read_text(encoding="utf-8")), encoding="utf-8")

    def test_request_fixtures_select_only_explicit_skills(self):
        cases = json.loads((ROOT / "tools/fixtures/hooks/prompts.json").read_text(encoding="utf-8"))
        self.assertTrue(cases)
        for case in cases:
            with self.subTest(prompt=case["prompt"]):
                result = self.decide(case["prompt"])
                self.assertEqual(case["rules"], result["rule_ids"])
                self.assertIn("Assay skill check", result["context"])
                self.assertLessEqual(len(result["rule_ids"]), 2)

    def test_ordinary_wording_in_any_language_gets_the_same_check_and_no_selection(self):
        prompts = ("Research alternatives using subagents", "Найди готовые плагины для этого",
                   "Поищи, есть ли что-то готовое", "Encuentra complementos existentes",
                   "既存のプラグインを探して", "Как это сделать в десктопном приложении?", "2 + 2",
                   "Implement SECRET_SENTINEL")
        results = [self.decide(prompt) for prompt in prompts]
        for prompt, result in zip(prompts, results):
            with self.subTest(prompt=prompt):
                self.assertEqual([], result["rule_ids"])
                self.assertEqual(results[0]["context"], result["context"])
        text = results[0]["context"]
        self.assertTrue(text.isascii())
        self.assertNotIn("SECRET_SENTINEL", text)
        self.assertIn('"Assay: none"', text)
        self.assertIn("grants no authority", text)
        self.assertLessEqual(len(text), activation.MAX_CHECK)

    def test_check_names_every_installed_skill_once(self):
        listed = self.listed(self.decide("anything")["context"])
        self.assertEqual(sorted(name.split("/", 1)[1] for name in self.skills), sorted(listed))
        self.assertEqual(len(listed), len(set(listed)))

    def test_disabled_or_missing_skill_leaves_the_check_and_its_explicit_choice(self):
        rules, fingerprint = activation.load_rules(self.root, disabled_skills=["skill/route-subagents"])
        self.assertNotEqual(self.fingerprint, fingerprint)
        self.assertNotIn("route-subagents", self.listed(self.decide("x", rules)["context"]))
        self.assertEqual([], self.decide("$route-subagents", rules)["rule_ids"])
        (self.root / "skills/route-subagents/SKILL.md").unlink()
        rules, _ = activation.load_rules(self.root)
        self.assertNotIn("route-subagents", self.listed(self.decide("x", rules)["context"]))
        self.assertEqual(["explicit:skill/code-change"], self.decide("Use code-change", rules)["rule_ids"])

    def test_check_can_be_disabled_and_retired_rule_ids_stay_valid(self):
        rules, fingerprint = activation.load_rules(self.root, disabled_rules=["skill-check"])
        self.assertNotEqual(self.fingerprint, fingerprint)
        self.assertEqual({"rule_ids": [], "context": ""}, self.decide("Найди готовые плагины", rules))
        selected = self.decide("Use code-change", rules)
        self.assertEqual(["explicit:skill/code-change"], selected["rule_ids"])
        self.assertNotIn("Assay skill check", selected["context"])
        retired, _ = activation.load_rules(self.root, disabled_rules=["delegation", "research", "reuse-lookup"])
        self.assertIn("Assay skill check", self.decide("x", retired)["context"])
        with self.assertRaises(ValueError):
            activation.load_rules(self.root, disabled_rules=["no-such-rule"])

    def test_a_subagent_gets_its_own_check_at_start(self):
        # A subagent never receives the per-request check; its start carries one.
        def start(agent_type, rules=None):
            return activation.evaluate({"hook_event_name": "SubagentStart", "agent_id": "a1",
                                        "agent_type": agent_type}, self.rules if rules is None else rules)
        text = start("general-purpose")["context"]
        self.assertIn("Assay skill check for this subagent", text)
        self.assertIn("skills your packet names apply", text)
        self.assertIn("Start your report", text)
        self.assertIn(str((self.root / "skills").resolve()), text)
        self.assertEqual(sorted(name.split("/", 1)[1] for name in self.skills), sorted(self.listed(text)))
        self.assertEqual(text, start("assay:evidence-reviewer")["context"])
        self.assertEqual("", start("assay-routing-advisor-high-0123456789abcdef")["context"])
        disabled, _ = activation.load_rules(self.root, disabled_rules=["skill-check"])
        self.assertEqual("", start("general-purpose", disabled)["context"])
        self.assertEqual("", activation.evaluate({"hook_event_name": "SubagentStop", "agent_id": "a1"},
                                                 self.rules)["context"])

    def test_skill_map_must_cover_the_catalog_with_short_ascii_cues(self):
        for label, transform in (
            ("missing", lambda text: text.replace('skill = "skill/code-change"', 'skill = "skill/test-writing"')),
            ("schema", lambda text: text.replace("schema = 2", "schema = 1")),
            ("non-ascii", lambda text: text.replace("writing or repairing tests", "написание тестов")),
            ("long", lambda text: text.replace("writing or repairing tests", "x" * (activation.MAX_CUE + 1))),
            ("patterns", lambda text: text.replace('cue = "writing or repairing tests"',
                                                   "cue = \"tests\"\npatterns = ['^x']")),
        ):
            with self.subTest(label=label):
                original = (self.root / "hooks/activation-rules.toml").read_text(encoding="utf-8")
                self.write_map(transform)
                with self.assertRaises(ValueError):
                    activation.load_rules(self.root)
                (self.root / "hooks/activation-rules.toml").write_text(original, encoding="utf-8")

    def test_explicit_context_is_english_bounded_and_not_authorization(self):
        event = {"hook_event_name": "UserPromptSubmit", "prompt": "Используй route-subagents для SECRET_SENTINEL"}
        original = copy.deepcopy(event)
        result = activation.evaluate(event, self.rules)
        self.assertEqual(original, event)
        self.assertEqual({"rule_ids", "context"}, set(result))
        self.assertEqual(["explicit:skill/route-subagents"], result["rule_ids"])
        hint = activation.context(result["rule_ids"], self.rules)
        self.assertIn("before substantial solo work", hint)
        self.assertIn("already-authorized", hint)
        self.assertIn("read-only", hint)
        self.assertNotIn("SECRET_SENTINEL", result["context"])
        self.assertTrue(result["context"].isascii())
        self.assertLessEqual(len(hint), activation.MAX_CONTEXT)

    def test_restore_preserves_relevance_check_not_authority(self):
        text = activation.context(["explicit:skill/evidence-research", "explicit:skill/route-subagents"],
                                  self.rules, restored=True)
        self.assertIn("Previous request", text)
        self.assertIn("Recheck relevance", text)
        self.assertIn("already-authorized", text)
        self.assertLessEqual(len(text), activation.MAX_CONTEXT)

    def test_non_prompt_events_do_not_create_new_intent(self):
        for name in ("PreToolUse", "PostToolUse", "SessionStart", "PostCompact"):
            with self.subTest(name=name):
                result = activation.evaluate({"hook_event_name": name, "prompt": "Use code-change"}, self.rules)
                self.assertEqual({"rule_ids": [], "context": ""}, result)

    def test_modified_method_invalidates_the_fingerprint(self):
        path = self.root / "skills/route-subagents/SKILL.md"
        path.write_text(path.read_text(encoding="utf-8") + "Changed procedure\n", encoding="utf-8")
        self.assertNotEqual(self.fingerprint, activation.load_rules(self.root)[1])


class DelegationReminderTests(unittest.TestCase):
    def test_session_reminder_reaches_planning_before_launch(self):
        for source in ("startup", "resume", "clear", "compact", "fork"):
            for environment, routing in (({}, False), ({"ASSAY_ROUTING_CONFIG": "routing.json"}, True)):
                with self.subTest(source=source, routing=routing):
                    result = reminders.reminder({"hook_event_name": "SessionStart", "source": source}, environment)
                    output = result["hookSpecificOutput"]
                    self.assertEqual({"hookEventName", "additionalContext"}, set(output))
                    self.assertIn("before substantial solo work", output["additionalContext"])
                    self.assertIn("does not authorize delegation", output["additionalContext"])
                    self.assertIn("workers must not spawn", output["additionalContext"])
                    self.assertLessEqual(len(output["additionalContext"]), 1200)

    def test_planning_reaches_delegation_requests_in_any_wording(self):
        # No hook recognizes delegation wording; the session reminder carries
        # the planning step, so whatever the wording it arrives before the agent
        # starts solo work.
        rules, _ = activation.load_rules(ROOT)
        session = reminders.reminder({"hook_event_name": "SessionStart", "source": "startup"}, {})
        session_text = session["hookSpecificOutput"]["additionalContext"]
        for prompt in ("Use subagents", "Research alternatives using subagents.",
                       "Можешь использовать субагентов для этого ревью.",
                       "Run this with subagents in parallel.",
                       "Распараллель это через агентов.",
                       "Use a workflow to review the diff."):
            with self.subTest(prompt=prompt):
                decision = activation.evaluate({"hook_event_name": "UserPromptSubmit", "prompt": prompt}, rules)
                channels = (session_text, decision.get("context") or "")
                self.assertTrue(any("before substantial solo work" in text for text in channels))

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
