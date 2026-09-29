"""Hook review regressions; no model calls or claims of native execution."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import activation, events, state
from route_evidence.pipeline_store import PipelineStore
from skill_reminder import reminder


def rule_fixture():
    # Actual input matchers; the expected selections below are authored separately.
    return tomllib.loads((ROOT / "hooks/activation-rules.toml").read_text(encoding="utf-8"))["rules"]


class HookLanguageTests(unittest.TestCase):
    def setUp(self):
        self.rules = rule_fixture()

    def test_input_languages_produce_identical_english_model_context(self):
        pairs = (
            ("Review tests", "Проведи ревью тестов", "test-audit"),
            ("Write tests", "Напиши тесты", "test-writing"),
            ("Research existing solutions", "Исследуй существующие решения", "research"),
            ("Create an implementation plan", "Составь план реализации", "planning"),
            ("Review the implementation", "Проведи ревью реализации", "audit"),
            ("Build an interface", "Создай интерфейс", "ui-delivery"),
            ("Implement the changes", "Внеси изменения", "code-change"),
        )
        for english, russian, expected in pairs:
            with self.subTest(rule=expected):
                outputs = [activation.evaluate({"hook_event_name": "UserPromptSubmit", "prompt": prompt}, self.rules)
                           for prompt in (english, russian)]
                self.assertEqual([expected], outputs[0]["rule_ids"])
                self.assertEqual(outputs[0], outputs[1])
                self.assertIn("Preserve the user's scope", outputs[1]["context"])
                self.assertNotRegex(outputs[1]["context"], r"[\u0400-\u04ff]")
                self.assertLessEqual(len(outputs[1]["context"]), activation.MAX_CONTEXT)

    def test_english_explicit_selection_and_native_identifier_spellings(self):
        for prompt in (
            "Use the skill code-change", "Use the code-change skill", "Apply skills code-change",
            "Use `assay:code-change`", "Use `$code-change`", "Use `/assay:code-change`",
        ):
            with self.subTest(prompt=prompt):
                self.assertEqual(["code-change"], [r["id"] for r in activation.select(prompt, self.rules)])
        selected = activation.select("Apply the skills `independent-audit` and `code-change`", self.rules)
        self.assertEqual(["audit", "code-change"], [r["id"] for r in selected])

    def test_explicit_selection_still_abstains_for_quoted_and_negative_requests(self):
        for prompt in (
            '> Use the skill code-change', '"Use the skill code-change"',
            "Do not use the skill code-change", "Не используй навык code-change",
            "Explain how to use `$code-change`", "Use `unknown-skill`",
        ):
            with self.subTest(prompt=prompt):
                self.assertEqual([], activation.select(prompt, self.rules))

    def test_legacy_and_restored_context_remain_english(self):
        for event in (
            {"hook_event_name": "SessionStart", "source": "startup"},
            {"hook_event_name": "PreToolUse", "tool_name": "Agent"},
            {"hook_event_name": "PreToolUse", "tool_name": "spawn_agent"},
        ):
            text = reminder(event, {})["hookSpecificOutput"]["additionalContext"]
            self.assertIn("route-subagents", text)
            self.assertNotRegex(text, r"[\u0400-\u04ff]")
        text = activation.context(["audit"], self.rules, restored=True)
        self.assertIn("Previous request suggested independent-audit", text)
        self.assertNotRegex(text, r"[\u0400-\u04ff]")


class HookDeliveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name) / "state"
        self.now = 1000.0
        self.rules = rule_fixture()
        self.base = {"session_id": "session", "cwd": "workspace", "transcript_path": "parent"}

    def apply(self, event, ids=(), *, fingerprint="revision-one", outcome=None, text="", client="codex"):
        decision = {"rule_ids": list(ids), "context": text or activation.context(ids, self.rules)}
        return state.apply({**self.base, **event}, client, decision, self.rules, fingerprint,
                           self.directory, clock=lambda: self.now, outcome=outcome)

    def prompt(self, turn, ids=(), **kwargs):
        return self.apply({"hook_event_name": "UserPromptSubmit", "turn_id": turn}, ids, **kwargs)

    def stored(self):
        with PipelineStore(self.directory, clock=lambda: self.now).transaction() as tx:
            return tx.get("hook-context", events.identity(self.base, "codex"))

    def restore(self):
        self.apply({"hook_event_name": "PostCompact"})
        return self.apply({"hook_event_name": "PreToolUse", "tool_name": "spawn_agent", "tool_use_id": "fresh"})

    def test_old_prompt_redelivery_cannot_replace_current_task(self):
        self.prompt("old", ["research"])
        self.now += 1
        self.prompt("new", ["code-change"])
        before = self.stored()
        self.now += 1
        self.assertEqual("", self.prompt("old", ["research"])["context"])
        self.assertEqual(before, self.stored())
        self.assertEqual(["code-change"], self.restore()["rule_ids"])

    def test_silent_prompt_redelivery_cannot_clear_current_task(self):
        self.prompt("explanation")
        self.prompt("implementation", ["code-change"])
        before = self.stored()
        self.prompt("explanation")
        self.assertEqual(before, self.stored())
        self.assertEqual(["code-change"], self.restore()["rule_ids"])

    def test_delivery_identity_is_not_changed_by_rule_revision(self):
        self.prompt("old", ["research"])
        self.prompt("new", ["code-change"], fingerprint="revision-two")
        before = self.stored()
        replayed = self.prompt("old", ["audit"], fingerprint="revision-two")
        self.assertEqual("", replayed["context"])
        self.assertEqual(before, self.stored())

    def test_replay_cannot_cancel_pending_compaction_restore(self):
        self.prompt("turn", ["research"])
        self.apply({"hook_event_name": "PostCompact"})
        self.prompt("turn", ["research"])
        self.assertTrue(self.stored().get("pending_restore"))
        output = self.apply({"hook_event_name": "PreToolUse", "tool_name": "spawn_agent", "tool_use_id": "next"})
        self.assertIn("evidence-research", output["context"])

    def test_guard_response_does_not_consume_an_undelivered_hint(self):
        for outcome in ("deny", "guard"):
            with self.subTest(outcome=outcome):
                self.prompt(outcome, ["audit"])
                self.apply({"hook_event_name": "PostCompact"})
                event = {"hook_event_name": "PreToolUse", "tool_name": "spawn_agent", "tool_use_id": outcome}
                self.assertEqual("", self.apply(event, outcome=outcome)["context"])
                self.assertTrue(self.stored().get("pending_restore"))
                # A later valid delivery is not suppressed by the earlier guard.
                self.assertIn("independent-audit", self.apply(event)["context"])

    def test_new_turn_and_claude_without_turn_identity_are_not_suppressed(self):
        self.assertTrue(self.prompt("one", ["audit"])["context"])
        self.assertTrue(self.prompt("two", ["audit"])["context"])
        for _ in range(2):
            result = self.apply({"hook_event_name": "UserPromptSubmit", "prompt": "same words"},
                                ["audit"], client="claude")
            self.assertTrue(result["context"])

    def test_guard_does_not_replace_the_required_session_message(self):
        self.prompt("one", ["audit"])
        result = self.apply({"hook_event_name": "SessionStart", "source": "resume"}, outcome="guard")
        self.assertEqual("", result["context"])
        self.assertEqual(["audit"], self.stored()["rules"])


class HookCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from runtime import cli
        cls.cli = cli

    def run_command(self, command, raw):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.json"
            path.write_text(raw, encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = self.cli.main([command, "--client", "codex", "--input", str(path)])
            self.assertEqual(raw, path.read_text(encoding="utf-8"))
            return code, stdout.getvalue(), stderr.getvalue()

    def test_optional_rule_failure_preserves_session_and_launch_reminders(self):
        for event in (
            {"hook_event_name": "SessionStart", "source": "startup"},
            {"hook_event_name": "PreToolUse", "tool_name": "Agent"},
        ):
            with self.subTest(event=event), patch.object(self.cli, "load_rules", side_effect=ValueError("SECRET")):
                result, error = self.cli.process(event, "claude", {})
            self.assertEqual(reminder(event, {}), result)
            self.assertNotIn("SECRET", error)
            self.assertNotRegex(error, r"[\u0400-\u04ff]")

    def test_guard_rewrite_keeps_restoration_pending_through_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            environment = {"PLUGIN_DATA": str(Path(temporary) / "state")}
            event = {"hook_event_name": "UserPromptSubmit", "session_id": "session", "cwd": "work",
                     "transcript_path": "parent", "turn_id": "turn", "prompt": "Review changes"}
            self.cli.process(event, "codex", environment)
            self.cli.process({**event, "hook_event_name": "PostCompact"}, "codex", environment)
            pre = {**event, "hook_event_name": "PreToolUse", "tool_name": "spawn_agent", "tool_use_id": "spawn"}
            protected = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": {"message": "kept"}}}
            with patch.object(self.cli, "routing_result", return_value=protected):
                result, error = self.cli.process(pre, "codex", environment)
            self.assertIsNone(error)
            self.assertEqual(protected, result)
            result, error = self.cli.process(pre, "codex", environment)
            self.assertIsNone(error)
            self.assertIn("independent-audit", result["hookSpecificOutput"]["additionalContext"])

    def test_optional_state_failure_preserves_basic_reminder(self):
        with tempfile.TemporaryDirectory() as temporary:
            event = {"hook_event_name": "PreToolUse", "tool_name": "Agent"}
            with patch.object(self.cli.state, "apply", side_effect=RuntimeError("SECRET")):
                result, error = self.cli.process(event, "claude", {"PLUGIN_DATA": temporary})
            self.assertEqual(reminder(event, {}), result)
            self.assertNotIn("SECRET", error)

    def test_preflight_exit_codes_separate_match_conflict_and_missing_evidence(self):
        valid = {"expected": {"model": "worker", "effort": "low"},
                 "supplied": {"model": "worker", "reasoning_effort": "low"},
                 "spawn_fields": {"model": "model", "effort": "reasoning_effort"},
                 "tool_schema": {"properties": {"model": {}, "reasoning_effort": {"enum": ["low", "high"]}}}}
        conflict = {**valid, "definition": {"model_reasoning_effort": "high"}}
        missing = {"expected": valid["expected"], "supplied": {}}
        for value, expected in ((valid, 0), (conflict, 1), (missing, 2)):
            with self.subTest(expected=expected):
                code, stdout, stderr = self.run_command("route-preflight", json.dumps(value))
                self.assertEqual(expected, code, stderr)
                report = json.loads(stdout)
                self.assertFalse(report["launch_verified"])
                self.assertIsNone(report["observed_effort"])

    def test_preflight_invalid_input_is_not_a_configuration_conflict(self):
        code, stdout, stderr = self.run_command("route-preflight", "[]")
        self.assertEqual(2, code)
        self.assertEqual("", stdout)
        self.assertTrue(stderr)

    def test_replay_rejects_empty_unknown_and_failed_inputs(self):
        for raw in ("", '{"hook_event_name":"not-a-client-event"}\n'):
            with self.subTest(raw=raw):
                code, _, _ = self.run_command("replay", raw)
                self.assertEqual(2, code)
        with patch.object(self.cli, "load_rules", side_effect=ImportError("SECRET")):
            code, stdout, _ = self.run_command("replay", '{"hook_event_name":"UserPromptSubmit","prompt":"Implement"}\n')
        self.assertEqual(2, code)
        self.assertNotIn("SECRET", stdout)

    def test_valid_silent_replay_is_not_confused_with_no_evidence(self):
        code, stdout, stderr = self.run_command("replay", '{"hook_event_name":"UserPromptSubmit","prompt":"Explain hooks"}\n')
        self.assertEqual(0, code, stderr)
        report = json.loads(stdout)
        self.assertEqual({}, report["result"])
        self.assertEqual("synthetic_replay", report["evidence"])

    def test_hook_json_reuses_strict_decoder(self):
        for raw in ('{"record_events":false,"record_events":true}', '{"value":NaN}'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "input.json"
                path.write_text(raw, encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.cli.read_json(path)


if __name__ == "__main__":
    unittest.main()
