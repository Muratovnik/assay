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
                for prompt, primary in (
                    ("Use subagents; research alternatives", "research"),
                    ("Use subagents to review this PR", "audit"),
                    ("Используй субагентов и составь план", "planning"),
                    ("Use subagents. Use code-change", "code-change"),
                ):
                    with self.subTest(prompt=prompt):
                        self.assertEqual([primary], self.decide(prompt, rules)["rule_ids"])
                self.assertEqual([], self.decide("Use subagents; explain the options; implement later", rules)["rule_ids"])
                self.assertEqual([], self.decide("Use subagents", rules)["rule_ids"])
                self.assertEqual([], self.decide("$route-subagents", rules)["rule_ids"])

    def test_missing_optional_skill_never_produces_a_delegation_hint(self):
        (self.root / "skills/route-subagents/SKILL.md").unlink()
        rules, _ = activation.load_rules(self.root)
        self.assertEqual(["planning"], self.decide("Create a plan; use subagents", rules)["rule_ids"])
        for prompt, primary in (
            ("Use subagents; research alternatives", "research"),
            ("Use subagents to review this PR", "audit"),
            ("Используй субагентов и составь план", "planning"),
        ):
            with self.subTest(prompt=prompt):
                self.assertEqual([primary], self.decide(prompt, rules)["rule_ids"])
        self.assertEqual([], self.decide("Use subagents", rules)["rule_ids"])

    def test_leading_directive_cannot_restore_a_disabled_primary_skill(self):
        for options in (
            {"disabled_rules": ["delegation", "audit"]},
            {"disabled_skills": ["skill/route-subagents", "skill/independent-audit"]},
        ):
            with self.subTest(options=options):
                rules, _ = activation.load_rules(self.root, **options)
                self.assertEqual([], self.decide("Use subagents; review this PR", rules)["rule_ids"])

    def test_primary_selection_uses_catalog_grammar_even_when_hint_is_disabled(self):
        rules, before = activation.load_rules(self.root, disabled_rules=["delegation"])
        self.assertEqual(["research"], self.decide("Use subagents; research alternatives", rules)["rule_ids"])
        path = self.root / "hooks/activation-rules.toml"
        path.write_text(path.read_text(encoding="utf-8").replace("use|launch|spawn", "dispatch|launch|spawn"), encoding="utf-8")
        rules, after = activation.load_rules(self.root, disabled_rules=["delegation"])
        self.assertNotEqual(before, after)
        self.assertEqual([], self.decide("Use subagents; research alternatives", rules)["rule_ids"])
        self.assertEqual(["research"], self.decide("Dispatch subagents; research alternatives", rules)["rule_ids"])

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


    def test_descriptions_and_reported_commands_do_not_request_workers(self):
        for text in (
            "Documentation about working with subagents",
            "The report describes work with subagents",
            "Документ описывает работу с субагентами",
            "Read this example and use subagents as a phrase in it",
            "Document the instruction and use subagents as an example",
            "Write a guide about working with subagents",
            "Write a note on using subagents",
            "Напиши руководство о работе с субагентами",
        ):
            with self.subTest(text=text):
                self.assertEqual([], self.decide(text)["rule_ids"])
                self.assertEqual(["code-change"], self.decide("Implement the parser. " + text)["rule_ids"])

    def test_reviewing_a_delegation_guide_does_not_request_delegation(self):
        for text in (
            "Review documentation about using subagents",
            "Review examples of working with subagents",
            "Review how to work with subagents",
        ):
            with self.subTest(text=text):
                self.assertEqual(["audit"], self.decide(text)["rule_ids"])
        for text in ("Use subagents as an example", "Используй субагентов как пример"):
            with self.subTest(text=text):
                self.assertEqual([], self.decide(text)["rule_ids"])
        self.assertEqual(["delegation"], self.decide("Use subagents as reviewers")["rule_ids"])

    def test_opaque_data_cannot_join_a_delegation_command(self):
        for opening, closing in (("`", "`"), ('"', '"'), ("«", "»"), ("“", "”"), ("‘", "’")):
            with self.subTest(opening=opening):
                self.assertEqual([], self.decide(f"Use {opening}not{closing} subagents")["rule_ids"])
                self.assertEqual([], self.decide(f"Используй {opening}не{closing} субагентов")["rule_ids"])
                result = self.decide(f"Research {opening}Package A{closing} using subagents")
                self.assertEqual(["research", "delegation"], result["rule_ids"])
        # Excluding a payload must not reveal a second command inside that payload.
        result = self.decide('Implement the parser; “example and use subagents” is data')
        self.assertEqual(["code-change"], result["rule_ids"])

    def test_conflicting_prohibitions_suppress_only_the_delegation_hint(self):
        prohibitions = (
            "Don't launch any subagents yet",
            "Don’t launch any subagents yet",
            "Do not use the subagents",
            "Never spawn any more agents",
            "Do not delegate verification to subagents",
            "Without the help of subagents",
            "Не нужно запускать субагентов",
            "Не надо использовать субагентов",
            "Не следует делегировать проверку субагентам",
            "Не используйте субагентов",
            "Без использования субагентов",
        )
        for prohibition in prohibitions:
            with self.subTest(prohibition=prohibition):
                self.assertEqual([], self.decide("Use subagents. " + prohibition)["rule_ids"])
                self.assertEqual(["research"], self.decide("Research alternatives using subagents. " + prohibition)["rule_ids"])
                self.assertEqual(["research"], self.decide("Use subagents; research alternatives. " + prohibition)["rule_ids"])
                self.assertEqual(["audit"], self.decide("Use subagents; review this PR. " + prohibition)["rule_ids"])
        for restriction in ("Don't modify files", "Do not repeat the workers' research", "Не меняй файлы"):
            with self.subTest(restriction=restriction):
                self.assertEqual(["research", "delegation"],
                                 self.decide("Research alternatives using subagents. " + restriction)["rule_ids"])

    def test_possessives_are_not_unmatched_quotations(self):
        for text in (
            "Research alternatives with subagents; preserve workers' budgets",
            "Research alternatives with subagents; preserve workers’ budgets",
            "Research the client's options using subagents",
            "Research the client’s options using subagents",
        ):
            with self.subTest(text=text):
                self.assertEqual(["research", "delegation"], self.decide(text)["rule_ids"])
        for opening in ('"', "«", "“", "‘"):
            self.assertEqual(["research"],
                             self.decide("Research alternatives; " + opening + "use subagents")["rule_ids"])

    def test_leading_delegation_preserves_the_first_workflow(self):
        for text, expected in (
            ("Use subagents; research alternatives; implement the result", ["research", "delegation"]),
            ("Use subagents to research alternatives", ["research", "delegation"]),
            ("Используй субагентов и составь план", ["planning", "delegation"]),
            ("Use subagents. Use code-change", ["code-change", "delegation"]),
            ("Use subagents; explain the tradeoffs; implement later", ["delegation"]),
            ("Use subagents; 'research alternatives' is an example", ["delegation"]),
        ):
            with self.subTest(text=text):
                self.assertEqual(expected, self.decide(text)["rule_ids"])

    def test_other_rules_for_the_same_skill_do_not_mask_a_match(self):
        extra = {"id": "other-delegation", "skill": "skill/route-subagents",
                 "priority": 1000, "patterns": [r"^Dispatch workers$"]}
        rules = [extra, *self.rules]
        self.assertEqual(["delegation"], self.decide("Use subagents", rules)["rule_ids"])
        self.assertEqual(["other-delegation"], self.decide("Dispatch workers", rules)["rule_ids"])

    def test_technical_arguments_preserve_direct_delegation_requests(self):
        for prompt in (
            "Review activation.py with subagents",
            "Review README.md using subagents",
            "Review https://github.com/Muratovnik/assay/pull/15 with subagents",
            "Review version 1.2 with subagents",
            "Проведи ревью activation.py с помощью субагентов",
            "Проведи ревью https://github.com/Muratovnik/assay/pull/15 с помощью субагентов",
            "Проведи ревью версии 1.2 с субагентами",
        ):
            with self.subTest(prompt=prompt):
                self.assertEqual(["audit", "delegation"], self.decide(prompt)["rule_ids"])
        for prompt in (
            "Delegate the review of activation.py to subagents",
            "Делегируй ревью activation.py субагентам",
        ):
            with self.subTest(prompt=prompt):
                self.assertEqual(["delegation"], self.decide(prompt)["rule_ids"])

    def test_technical_arguments_do_not_turn_mentions_into_delegation(self):
        for prompt in (
            "Review README.md about using subagents",
            "Review version 1.2 without subagents",
            "Review activation.py with subagents. Do not launch any subagents",
            "Review activation.py with subagents. Do not delegate verification of activation.py to subagents",
            "Review README.md. Documentation with subagents",
            'Review README.md. "Use subagents" is an example',
            "Review README.md. `Use subagents` is an example",
            "Проведи ревью activation.py без использования субагентов",
            "Проведи ревью activation.py с помощью субагентов. Не следует делегировать проверку activation.py субагентам",
        ):
            with self.subTest(prompt=prompt):
                self.assertEqual(["audit"], self.decide(prompt)["rule_ids"])

    def test_subject_conjunctions_do_not_hide_the_workflow_modifier(self):
        for text in (
            "Research X and Y using subagents",
            "Research alternatives and use subagents",
            "Сравни X и Y с помощью субагентов",
            "Сравни варианты и используй субагентов",
        ):
            with self.subTest(text=text):
                self.assertEqual(["research", "delegation"], self.decide(text)["rule_ids"])


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
