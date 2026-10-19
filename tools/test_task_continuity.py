"""Continuation hint state under native-shaped events, not model adherence."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import activation, state
from runtime.cli import process
from route_evidence.pipeline_store import PipelineStore


class ContinuationGrammarTests(unittest.TestCase):
    def test_plain_whole_request_can_continue(self):
        for prompt in ("continue", "Resume.", "go on!", "go ahead", "Please, continue.",
                       "продолжай", "Продолжи!", "пожалуйста, продолжай", "продолжим"):
            with self.subTest(prompt=prompt):
                self.assertTrue(activation.continuation_request(prompt))

    def test_tasks_restrictions_and_embedded_examples_do_not_inherit(self):
        for prompt in ("continue with another project", "continue, but only review", "yes",
                       "продолжай, но только анализ", "не продолжай", "What does continue mean?",
                       '"continue"', "`continue`", "**continue**", "> continue", "- continue",
                       "# continue", "```\ncontinue\n```", "continue\n\nOnly review now.",
                       "continue\nonly review", "continue <!-- note -->", None, {}):
            with self.subTest(prompt=prompt):
                self.assertFalse(activation.continuation_request(prompt))


class TaskContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.now = 1000.0
        self.rules, self.fingerprint = activation.load_rules(ROOT)
        self.event = {"hook_event_name": "UserPromptSubmit", "session_id": "session",
                      "cwd": str(self.directory / "work"), "transcript_path": "root-trace",
                      "turn_id": "turn-1", "prompt": "Use code-change for the agreed repair"}

    def apply(self, event=None, client="codex", **options):
        event = self.event if event is None else event
        return state.apply(event, client, activation.evaluate(event, self.rules),
                           self.rules, self.fingerprint, self.directory,
                           clock=lambda: self.now, **options)

    # The skill check names every skill on every prompt, so a retained
    # suggestion is identified by its own sentence, not by a skill name.
    RESTORED = "Previous request suggested "

    def test_continue_retains_suggestion_through_compaction_for_both_clients(self):
        for client in ("claude", "codex"):
            with self.subTest(client=client):
                first = self.apply(client=client)
                self.assertEqual(["explicit:skill/code-change"], first["rule_ids"])
                continued = self.apply({**self.event, "turn_id": "turn-2", "prompt": "Продолжай"}, client)
                self.assertEqual(first["rule_ids"], continued["rule_ids"])
                self.assertIn(self.RESTORED + "code-change", continued["context"])
                self.assertIn("Assay skill check", continued["context"])
                restored = self.apply({**self.event, "hook_event_name": "SessionStart",
                                       "source": "compact"}, client)
                self.assertIn(self.RESTORED + "code-change", restored["context"])

    def test_new_task_and_narrowed_request_replace_old_hint(self):
        self.apply()
        narrowed = self.apply({**self.event, "turn_id": "turn-2",
                               "prompt": "Continue, but only prepare a plan"})
        self.assertEqual([], narrowed["rule_ids"])
        self.assertNotIn(self.RESTORED, narrowed["context"])
        fresh = self.apply({**self.event, "turn_id": "turn-3",
                            "prompt": "Use independent-audit for this implementation"})
        self.assertEqual(["explicit:skill/independent-audit"], fresh["rule_ids"])
        # Unknown new requests clear rather than resurrect an earlier authority.
        cleared = self.apply({**self.event, "turn_id": "turn-4", "prompt": "A different question"})
        self.assertEqual([], cleared["rule_ids"])
        self.assertEqual([], self.apply({**self.event, "turn_id": "turn-5", "prompt": "continue"})["rule_ids"])

    def test_continue_without_matching_live_state_is_silent(self):
        continued = {**self.event, "turn_id": "turn-2", "prompt": "continue"}
        self.assertNotIn(self.RESTORED, self.apply(continued)["context"])
        self.apply({**self.event, "turn_id": "turn-3"})
        self.now += state.TTL + 1
        late = self.apply({**continued, "turn_id": "turn-4"})
        self.assertEqual([], late["rule_ids"])
        self.assertNotIn(self.RESTORED, late["context"])

    def test_changed_method_bytes_and_clear_retire_suggestion(self):
        self.apply()
        continued = {**self.event, "turn_id": "turn-2", "prompt": "continue"}
        changed = state.apply(continued, "codex", activation.evaluate(continued, self.rules),
                              self.rules, "new-fingerprint", self.directory, clock=lambda: self.now)
        self.assertNotIn(self.RESTORED, changed["context"])
        self.apply({**self.event, "turn_id": "turn-3"})
        self.apply({**self.event, "hook_event_name": "SessionStart", "source": "clear"})
        self.assertNotIn(self.RESTORED, self.apply({**continued, "turn_id": "turn-4"})["context"])

    def test_duplicate_continue_cannot_revert_a_new_task(self):
        self.apply()
        continued = {**self.event, "turn_id": "turn-2", "prompt": "continue"}
        self.apply(continued)
        self.apply({**self.event, "turn_id": "turn-3", "prompt": "Use independent-audit for this implementation"})
        self.assertEqual("", self.apply(continued)["context"])
        restored = self.apply({**self.event, "hook_event_name": "SessionStart", "source": "compact"})
        self.assertIn(self.RESTORED + "independent-audit", restored["context"])
        self.assertNotIn("code-change", restored["context"])

    def test_other_workspaces_and_agents_cannot_inherit(self):
        self.apply()
        for changed in ({"cwd": "another"}, {"agent_id": "worker"}, {"session_id": "other"},
                        {"transcript_path": "worker-trace"}, {"transcript_path": None}):
            event = {**self.event, "turn_id": "turn-2", "prompt": "continue", **changed}
            with self.subTest(changed=changed):
                self.assertNotIn(self.RESTORED, self.apply(event)["context"])

    def test_guard_does_not_consume_or_authorize_continuation(self):
        self.apply()
        continued = {**self.event, "turn_id": "turn-2", "prompt": "continue"}
        self.assertEqual("", self.apply(continued, outcome="deny")["context"])
        self.assertIn(self.RESTORED + "code-change", self.apply(continued)["context"])

    def test_check_survives_a_missing_markdown_parser_with_and_without_state(self):
        from unittest.mock import patch
        settings = self.directory / "parserless.json"
        settings.write_text(json.dumps({"state_dir": str(self.directory / "parserless")}), encoding="utf-8")
        for environment in ({}, {"ASSAY_HOOK_CONFIG": str(settings)}):
            for client in ("claude", "codex"):
                event = {**self.event, "turn_id": f"{client}-{len(environment)}"}
                with self.subTest(client=client, stateful=bool(environment)), \
                        patch.dict(sys.modules, {"markdown_it": None}):
                    output, error = process(event, client, environment, clock=lambda: self.now)
                    self.assertIsNone(error)
                    context = output["hookSpecificOutput"]["additionalContext"]
                    # Without the parser an explicit choice is not recognized,
                    # but the check does not read the prompt and still arrives.
                    self.assertTrue(context.startswith("Assay skill check:"))
                    self.assertNotIn("The request suggests", context)

    def test_event_processing_reuses_existing_state_without_storing_prompt(self):
        settings = self.directory / "settings.json"
        settings.write_text(json.dumps({"state_dir": str(self.directory / "events")}), encoding="utf-8")
        environment = {"ASSAY_HOOK_CONFIG": str(settings)}
        for client in ("claude", "codex"):
            with self.subTest(client=client):
                output, error = process(self.event, client, environment, clock=lambda: self.now)
                self.assertIsNone(error)
                continued = {**self.event, "turn_id": "turn-2", "prompt": "continue"}
                output, error = process(continued, client, environment, clock=lambda: self.now)
                self.assertIsNone(error)
                self.assertEqual({"hookEventName", "additionalContext"}, set(output["hookSpecificOutput"]))
                self.assertIn(self.RESTORED + "code-change", output["hookSpecificOutput"]["additionalContext"])
        with PipelineStore(self.directory / "events", clock=lambda: self.now).transaction() as tx:
            saved = json.dumps([tx.values(kind) for kind in state.KINDS])
        self.assertNotIn(self.event["prompt"], saved)
        self.assertNotIn("skills_used", saved)


if __name__ == "__main__":
    unittest.main()
