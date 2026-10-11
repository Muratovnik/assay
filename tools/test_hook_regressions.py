"""Hook review regressions; no model calls or claims of native execution."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import activation, events, state
from route_evidence.pipeline_store import PipelineStore
from skill_reminder import reminder

# The skill check names every skill on every prompt, so a selection is
# identified by its own sentence or rule ids, never by a skill name alone.
SUGGESTS = "The request suggests "
RESTORED = "Previous request suggested "
CHECK = "Assay skill check:"


def rule_fixture():
    return activation.load_rules(ROOT)[0]


def prompt_event(prompt):
    return {"hook_event_name": "UserPromptSubmit", "prompt": prompt}


class HookLanguageTests(unittest.TestCase):
    def setUp(self):
        self.rules = rule_fixture()

    def test_ordinary_english_and_russian_prompts_produce_identical_context_and_no_selection(self):
        pairs = (
            ("Review tests", "Проведи ревью тестов"),
            ("Write tests", "Напиши тесты"),
            ("Research existing solutions", "Исследуй существующие решения"),
            ("Create an implementation plan", "Составь план реализации"),
            ("Build an interface", "Создай интерфейс"),
            ("Implement the changes", "Внеси изменения"),
            ("Use subagents", "Используй субагентов"),
        )
        for english, russian in pairs:
            with self.subTest(prompt=english):
                outputs = [activation.evaluate(prompt_event(prompt), self.rules) for prompt in (english, russian)]
                self.assertEqual(outputs[0], outputs[1])
                self.assertEqual([], outputs[0]["rule_ids"])
                self.assertNotIn(SUGGESTS, outputs[0]["context"])
                self.assertTrue(outputs[0]["context"].startswith(CHECK))
                self.assertTrue(outputs[0]["context"].isascii())

    def test_explicit_choice_selects_the_same_skill_in_both_languages(self):
        for english, russian, expected in (
            ("Use code-change", "Используй code-change", "code-change"),
            ("Apply the skill test-audit", "Примени навык test-audit", "test-audit"),
        ):
            with self.subTest(skill=expected):
                outputs = [activation.evaluate(prompt_event(prompt), self.rules) for prompt in (english, russian)]
                self.assertEqual(["explicit:skill/" + expected], outputs[0]["rule_ids"])
                self.assertEqual(outputs[0], outputs[1])
                self.assertIn(SUGGESTS + expected + ".", outputs[1]["context"])
                self.assertTrue(outputs[1]["context"].isascii())

    def test_english_explicit_selection_and_native_identifier_spellings(self):
        for prompt in (
            "Use the skill code-change", "Use the code-change skill", "Apply skills code-change",
            "Use `assay:code-change`", "Use `$code-change`", "Use `/assay:code-change`",
        ):
            with self.subTest(prompt=prompt):
                self.assertEqual(["explicit:skill/code-change"],
                                 [r["id"] for r in activation.select(prompt, self.rules)])
        selected = activation.select("Apply the skills `independent-audit` and `code-change`", self.rules)
        self.assertEqual(["explicit:skill/independent-audit", "explicit:skill/code-change"],
                         [r["id"] for r in selected])

    def test_explicit_selection_still_abstains_for_quoted_and_negative_requests(self):
        for prompt in (
            '> Use the skill code-change', '"Use the skill code-change"',
            "Do not use the skill code-change", "Не используй навык code-change",
            "Explain how to use `$code-change`", "Use `unknown-skill`",
        ):
            with self.subTest(prompt=prompt):
                self.assertEqual([], activation.select(prompt, self.rules))

    def test_legacy_and_restored_context_remain_english(self):
        routing = {"ASSAY_ROUTING_CONFIG": "routing.json"}
        for event, environment, expected in (
            ({"hook_event_name": "SessionStart", "source": "startup"}, {}, "Assay is installed."),
            ({"hook_event_name": "SessionStart", "source": "startup"}, routing, "route-subagents"),
            ({"hook_event_name": "PreToolUse", "tool_name": "Agent"}, {}, "route-subagents"),
            ({"hook_event_name": "PreToolUse", "tool_name": "spawn_agent"}, {}, "route-subagents"),
        ):
            text = reminder(event, environment)["hookSpecificOutput"]["additionalContext"]
            self.assertIn(expected, text)
            self.assertNotRegex(text, r"[\u0400-\u04ff]")
        text = activation.context(["explicit:skill/independent-audit"], self.rules, restored=True)
        self.assertIn(RESTORED + "independent-audit", text)
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
        self.prompt("old", ["explicit:skill/evidence-research"])
        self.now += 1
        self.prompt("new", ["explicit:skill/code-change"])
        before = self.stored()
        self.now += 1
        self.assertEqual("", self.prompt("old", ["explicit:skill/evidence-research"])["context"])
        self.assertEqual(before, self.stored())
        self.assertEqual(["explicit:skill/code-change"], self.restore()["rule_ids"])

    def test_silent_prompt_redelivery_cannot_clear_current_task(self):
        self.prompt("explanation")
        self.prompt("implementation", ["explicit:skill/code-change"])
        before = self.stored()
        self.prompt("explanation")
        self.assertEqual(before, self.stored())
        self.assertEqual(["explicit:skill/code-change"], self.restore()["rule_ids"])

    def test_delivery_identity_is_not_changed_by_rule_revision(self):
        self.prompt("old", ["explicit:skill/evidence-research"])
        self.prompt("new", ["explicit:skill/code-change"], fingerprint="revision-two")
        before = self.stored()
        replayed = self.prompt("old", ["explicit:skill/independent-audit"], fingerprint="revision-two")
        self.assertEqual("", replayed["context"])
        self.assertEqual(before, self.stored())

    def test_replay_cannot_cancel_pending_compaction_restore(self):
        self.prompt("turn", ["explicit:skill/evidence-research"])
        self.apply({"hook_event_name": "PostCompact"})
        self.prompt("turn", ["explicit:skill/evidence-research"])
        self.assertTrue(self.stored().get("pending_restore"))
        output = self.apply({"hook_event_name": "PreToolUse", "tool_name": "spawn_agent", "tool_use_id": "next"})
        self.assertIn(RESTORED + "evidence-research", output["context"])

    def test_guard_response_does_not_consume_an_undelivered_hint(self):
        for outcome in ("deny", "guard"):
            with self.subTest(outcome=outcome):
                self.prompt(outcome, ["explicit:skill/independent-audit"])
                self.apply({"hook_event_name": "PostCompact"})
                event = {"hook_event_name": "PreToolUse", "tool_name": "spawn_agent", "tool_use_id": outcome}
                self.assertEqual("", self.apply(event, outcome=outcome)["context"])
                self.assertTrue(self.stored().get("pending_restore"))
                # A later valid delivery is not suppressed by the earlier guard.
                self.assertIn(RESTORED + "independent-audit", self.apply(event)["context"])

    def test_new_turn_and_claude_without_turn_identity_are_not_suppressed(self):
        self.assertTrue(self.prompt("one", ["explicit:skill/independent-audit"])["context"])
        self.assertTrue(self.prompt("two", ["explicit:skill/independent-audit"])["context"])
        for _ in range(2):
            result = self.apply({"hook_event_name": "UserPromptSubmit", "prompt": "same words"},
                                ["explicit:skill/independent-audit"], client="claude")
            self.assertTrue(result["context"])

    def test_guard_does_not_replace_the_required_session_message(self):
        self.prompt("one", ["explicit:skill/independent-audit"])
        result = self.apply({"hook_event_name": "SessionStart", "source": "resume"}, outcome="guard")
        self.assertEqual("", result["context"])
        self.assertEqual(["explicit:skill/independent-audit"], self.stored()["rules"])


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

    def test_session_restore_keeps_baseline_with_or_without_a_matching_prompt(self):
        for client in ("claude", "codex"):
            for source in ("resume", "compact"):
                for prompt, suggested in (("Explain this text", False), ("Use code-change for this repair", True)):
                    with self.subTest(client=client, source=source, prompt=prompt), tempfile.TemporaryDirectory() as temporary:
                        env = {"PLUGIN_DATA": temporary}
                        base = {"session_id": "s", "cwd": "work", "transcript_path": "parent"}
                        self.cli.process({**base, "hook_event_name": "UserPromptSubmit", "prompt": prompt}, client, env)
                        result, error = self.cli.process({**base, "hook_event_name": "SessionStart", "source": source}, client, env)
                        self.assertIsNone(error)
                        context = result["hookSpecificOutput"]["additionalContext"]
                        self.assertIn("Assay is installed.", context)
                        self.assertIn("does not authorize delegation", context)
                        self.assertEqual(suggested, RESTORED + "code-change" in context)

    def test_session_compact_restore_consumes_pending_hint_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            env = {"PLUGIN_DATA": temporary}
            base = {"session_id": "s", "cwd": "work", "transcript_path": "parent"}
            self.cli.process({**base, "hook_event_name": "UserPromptSubmit", "prompt": "Use code-change for this repair"}, "codex", env)
            self.cli.process({**base, "hook_event_name": "PostCompact"}, "codex", env)
            result, error = self.cli.process({**base, "hook_event_name": "SessionStart", "source": "compact"}, "codex", env)
            self.assertIsNone(error)
            self.assertIn(RESTORED + "code-change", result["hookSpecificOutput"]["additionalContext"])
            result, error = self.cli.process({**base, "hook_event_name": "PreToolUse", "tool_name": "spawn_agent",
                                             "tool_use_id": "next"}, "codex", env)
            self.assertIsNone(error)
            self.assertIn("route-subagents", result["hookSpecificOutput"]["additionalContext"])
            self.assertNotIn(RESTORED, result["hookSpecificOutput"]["additionalContext"])

    def test_narrowed_request_replaces_pending_implementation_hint_in_both_clients(self):
        for client in ("codex", "claude"):
            for narrow, expected in (
                ("Используй implementation-planning; пока только план.", "implementation-planning"),
                ("Пока только составь план.", None),
                ("Do not change files. Explain the current state.", None),
            ):
                with self.subTest(client=client, narrow=narrow), tempfile.TemporaryDirectory() as temporary:
                    env = {"PLUGIN_DATA": temporary}
                    base = {"session_id": "narrowed", "cwd": "work", "transcript_path": "parent"}
                    self.cli.process({**base, "hook_event_name": "UserPromptSubmit", "turn_id": "old",
                                      "prompt": "Use code-change for this repair"}, client, env)
                    self.cli.process({**base, "hook_event_name": "PostCompact"}, client, env)
                    self.cli.process({**base, "hook_event_name": "UserPromptSubmit", "turn_id": "new",
                                      "prompt": narrow}, client, env)
                    self.cli.process({**base, "hook_event_name": "PostCompact"}, client, env)
                    result, error = self.cli.process({**base, "hook_event_name": "SessionStart",
                                                      "source": "resume"}, client, env)
                    self.assertIsNone(error)
                    context = result["hookSpecificOutput"]["additionalContext"]
                    self.assertNotIn(RESTORED + "code-change", context)
                    if expected:
                        self.assertIn(RESTORED + expected, context)
                    else:
                        self.assertNotIn(RESTORED, context)

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
                     "transcript_path": "parent", "turn_id": "turn", "prompt": "Use independent-audit for this review"}
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
            self.assertIn(RESTORED + "independent-audit", result["hookSpecificOutput"]["additionalContext"])

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

    def test_valid_unselected_replay_is_not_confused_with_no_evidence(self):
        code, stdout, stderr = self.run_command("replay", '{"hook_event_name":"UserPromptSubmit","prompt":"Explain hooks"}\n')
        self.assertEqual(0, code, stderr)
        report = json.loads(stdout)
        self.assertIsNone(report["error"])
        context = report["result"]["hookSpecificOutput"]["additionalContext"]
        self.assertTrue(context.startswith(CHECK))
        self.assertNotIn(SUGGESTS, context)
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
