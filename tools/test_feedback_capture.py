"""Native contract fixtures and real local persistence, not model adherence evals."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import feedback, cli


class FeedbackCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.data = self.base / "data"
        self.now = 1000000.0
        self.settings = {"state_dir": str(self.data), "feedback_capture": "content"}

    def clock(self):
        return self.now

    def event(self, client, prompt="You missed the required static analysis.", turn="turn-1"):
        if client == "cursor":
            return {"hook_event_name": "beforeSubmitPrompt", "conversation_id": "conversation-1",
                    "generation_id": turn, "workspace_roots": [str(self.base / "project")], "prompt": prompt}
        return {"hook_event_name": "BeforeAgent" if client == "gemini" else "UserPromptSubmit",
                "session_id": "session-1", "cwd": str(self.base / "project"),
                "transcript_path": str(self.base / "never-read-this-transcript.jsonl"),
                **({"turn_id": turn} if client == "codex" else {}), "prompt": prompt}

    def capture(self, client="claude", event=None, settings=None):
        return feedback.handle(event or self.event(client), client, settings or self.settings, root=ROOT, clock=self.clock)

    def records(self):
        return feedback.read(self.data, clock=self.clock)

    def test_disabled_has_no_storage_or_parser_effect(self):
        with patch.object(feedback, "signal", side_effect=AssertionError("must not classify")):
            for client in ("claude", "codex", "gemini", "cursor"):
                self.assertEqual(self.capture(client, settings={"feedback_capture": "off"}), {})
        self.assertFalse(self.data.exists())
        self.assertEqual(cli.options({})["feedback_capture"], "off")

    def test_input_signals_and_nearby_valid_controls(self):
        for prompt in ("Ты упустил обязательную проверку.", "Нет, я просил исследование, а не реализацию.",
                       "Почему ты не проверил библиотеку?", "Я уже говорил не менять API.",
                       "That is incorrect.", "I asked for a review, not a patch.",
                       "No, you missed the constraint.", "Нет, это неправильно."):
            with self.subTest(prompt=prompt):
                self.assertIsNotNone(feedback.signal(prompt))
        for prompt in ("Add a linter.", "I changed my mind; use another library.",
                       "Explain why you might miss a requirement.", "No thanks.", "You missed nothing.",
                       "> You missed the check.", "```text\nYou missed the check.\n```",
                       "- You missed the check.", "Discuss this example:\n\nYou missed the check.",
                       '"You missed the check" is an example.', "    You missed the check."):
            with self.subTest(prompt=prompt):
                self.assertIsNone(feedback.signal(prompt))

    def test_native_context_envelopes(self):
        for client in ("claude", "codex", "gemini"):
            with self.subTest(client=client):
                output = self.capture(client)
                self.assertEqual(set(output), {"hookSpecificOutput"})
                fields = output["hookSpecificOutput"]
                expected = {"additionalContext"} if client == "gemini" else {"hookEventName", "additionalContext"}
                self.assertEqual(set(fields), expected)
                if client != "gemini":
                    self.assertEqual(fields["hookEventName"], "UserPromptSubmit")
                self.assertIn("not confirmed as an error", fields["additionalContext"])
                self.assertNotIn("You missed the required static analysis", fields["additionalContext"])
        self.assertEqual(len(self.records()), 3)

    def test_cursor_uses_only_documented_post_tool_context(self):
        event = self.event("cursor")
        self.assertEqual(self.capture("cursor", event), {})
        self.assertTrue(self.records()[0]["pending_notice"])
        unrelated = {**event, "hook_event_name": "postToolUse", "generation_id": "different-turn"}
        self.assertEqual(self.capture("cursor", unrelated), {})
        same = {**event, "hook_event_name": "postToolUse", "tool_use_id": "tool-1"}
        output = self.capture("cursor", same)
        self.assertEqual(set(output), {"additional_context"})
        self.assertIn(self.records()[0]["id"], output["additional_context"])
        self.assertEqual(self.capture("cursor", {**same, "tool_use_id": "tool-2"}), {})
        self.assertEqual(self.capture("cursor", event), {})
        self.assertEqual(len(self.records()), 1)

    def test_cursor_no_tools_needs_no_forced_followup_and_notice_expires(self):
        event = self.event("cursor")
        self.capture("cursor", event)
        self.now += 24 * 3600 + 1
        self.assertEqual(self.capture("cursor", {**event, "hook_event_name": "postToolUse"}), {})
        self.assertEqual(len(self.records()), 1)

    def test_native_ids_deduplicate_not_text(self):
        for client in ("codex", "cursor"):
            event = self.event(client)
            self.capture(client, event)
            self.capture(client, event)
            self.capture(client, self.event(client, turn="turn-2"))
        self.assertEqual(len(self.records()), 4)
        for client in ("claude", "gemini"):
            event = self.event(client)
            self.capture(client, event)
            self.capture(client, event)
        self.assertEqual(len(self.records()), 8)

    def test_workers_and_workspaces_do_not_share_candidates(self):
        event = self.event("codex")
        self.capture("codex", event)
        self.capture("codex", {**event, "agent_id": "worker-1"})
        self.capture("codex", {**event, "cwd": str(self.base / "other-project")})
        self.assertEqual(len(self.records()), 3)
        missing = {k: v for k, v in event.items() if k != "transcript_path"}
        self.assertEqual(self.capture("codex", missing), {})
        self.assertEqual(len(self.records()), 3)

    def test_metadata_mode_does_not_store_or_inject_text(self):
        prompt = "You missed the secret SENTINEL_PRIVATE_TEXT."
        output = self.capture(event=self.event("claude", prompt), settings={**self.settings, "feedback_capture": "metadata"})
        record = self.records()[0]
        self.assertNotIn("SENTINEL_PRIVATE_TEXT", json.dumps(record) + json.dumps(output))
        self.assertIsNone(record["excerpt"])
        with self.assertRaises(ValueError):
            feedback.annotate(self.data, record["id"], {"category": "uncertain", "basis": "unknown", "observed": prompt}, clock=self.clock)
        feedback.annotate(self.data, record["id"], {"category": "uncertain", "basis": "unknown"}, clock=self.clock)
        self.assertEqual(self.records()[0]["status"], "candidate")

    def test_content_is_bounded_and_provenance_is_immutable(self):
        prompt = "You missed the requirement. " + "x" * 5000
        self.capture(event=self.event("claude", prompt))
        before = copy.deepcopy(self.records()[0])
        self.assertEqual(before["excerpt"], prompt[:4096])
        self.assertTrue(before["excerpt_truncated"])
        data = {"category": "changed_requirement", "basis": "new_requirement", "expected": "A newly requested option."}
        feedback.annotate(self.data, before["id"], data, clock=self.clock)
        feedback.annotate(self.data, before["id"], data, clock=self.clock)
        after = self.records()[0]
        self.assertEqual(after["source"], before["source"])
        self.assertEqual(after["excerpt"], before["excerpt"])
        self.assertEqual(after["status"], "candidate")
        self.assertEqual(len(after["annotations"]), 1)
        self.assertEqual(after["expires_at"], before["expires_at"])
        self.assertEqual(after["source"]["evidence_level"], "command_input_unattested")

    def test_annotation_cannot_confirm_or_overwrite_source(self):
        self.capture()
        key = self.records()[0]["id"]
        for extra in ({"status": "confirmed"}, {"source": {}}, {"observed": "x" * 1501}):
            with self.subTest(extra=list(extra)):
                with self.assertRaises(ValueError):
                    feedback.annotate(self.data, key, {"category": "reported_mismatch", "basis": "prior_requirement", **extra}, clock=self.clock)
        self.assertEqual(self.records()[0]["annotations"], [])
        feedback.review(self.data, key, "confirmed", "Compared against the earlier requirement.", clock=self.clock)
        self.assertEqual(self.records()[0]["status"], "confirmed")
        self.assertEqual(self.records()[0]["review"]["provenance"], "explicit_local_review_unattested")
        with self.assertRaises(ValueError):
            feedback.review(self.data, key, "duplicate", "Same case.", duplicate_of=key, clock=self.clock)

    def test_expiry_capacity_and_delete_preserve_other_records(self):
        with patch.object(feedback, "MAX_RECORDS", 1):
            self.capture()
            key = self.records()[0]["id"]
            with self.assertRaises(ValueError):
                self.capture()
            self.assertEqual(self.records()[0]["id"], key)
        feedback.delete(self.data, key, clock=self.clock)
        self.assertEqual(self.records(), [])
        self.capture()
        self.now += 90 * 24 * 3600 + 1
        self.assertEqual(self.records(), [])
        self.assertFalse((self.data / "routing-v2.sqlite3").exists())
        self.assertTrue((self.data / "feedback" / "routing-v2.sqlite3").exists())

    def test_concurrent_delivery_is_transactionally_deduplicated(self):
        event = self.event("codex")
        with ThreadPoolExecutor(max_workers=6) as pool:
            outputs = list(pool.map(lambda _: self.capture("codex", event), range(6)))
        self.assertEqual(sum(bool(output) for output in outputs), 1)
        self.assertEqual(len(self.records()), 1)

    def test_invalid_event_and_missing_configuration(self):
        for client in ("claude", "codex", "gemini", "cursor"):
            self.assertEqual(self.capture(client, {"hook_event_name": "Stop"}), {})
        self.assertFalse(self.data.exists())
        with self.assertRaises(ValueError):
            self.capture(settings={"feedback_capture": "content"})
        with self.assertRaises(ValueError):
            self.capture(settings={"feedback_capture": "content", "state_dir": "relative"})

    def test_linked_state_path_does_not_write_to_target(self):
        target = self.base / "other-owner"
        target.mkdir()
        try:
            self.data.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("native directory symlink permission unavailable")
        with self.assertRaises(ValueError):
            self.capture()
        self.assertEqual(list(target.iterdir()), [])

    def test_integrated_native_plugin_entry_and_replay_default(self):
        config = self.base / "config.json"
        config.write_text(json.dumps(self.settings), encoding="utf-8")
        for client in ("claude", "codex"):
            result, error = cli.process(self.event(client), client, {"ASSAY_HOOK_CONFIG": str(config)}, clock=self.clock)
            self.assertIsNone(error)
            self.assertIn("feedback candidate", result["hookSpecificOutput"]["additionalContext"])
        before = len(self.records())
        cli.process(self.event("claude"), "claude", {}, clock=self.clock)
        self.assertEqual(len(self.records()), before)

    def test_optional_failure_preserves_hints_and_guard(self):
        base = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "Existing hint."}}
        with patch.object(cli, "_process", return_value=(base, None)), patch.object(feedback, "handle", side_effect=OSError("PRIVATE_PATH")):
            result, error = cli.process(self.event("claude"), "claude", {})
        self.assertEqual(result, base)
        self.assertNotIn("PRIVATE_PATH", error)
        guard = {"hookSpecificOutput": {"permissionDecision": "deny", "permissionDecisionReason": "Required guard."}}
        with patch.object(cli, "_process", return_value=(guard, None)), patch.object(feedback, "handle") as capture:
            result, error = cli.process(self.event("claude"), "claude", {})
            capture.assert_not_called()
        self.assertEqual(result, guard)
        self.assertIsNone(error)

    def test_existing_context_is_appended_not_replaced(self):
        base = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "Existing hint."}}
        extra = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "Feedback hint."}}
        with patch.object(cli, "_process", return_value=(base, None)), patch.object(feedback, "handle", return_value=extra):
            result, _ = cli.process(self.event("claude"), "claude", {})
        self.assertEqual(result["hookSpecificOutput"]["additionalContext"], "Existing hint.\nFeedback hint.")

    def run_cli(self, *args, payload="", ascii_stdout=False):
        environment = {key: value for key, value in os.environ.items()
                       if key not in {"ASSAY_HOOK_CONFIG", "ASSAY_ROUTING_CONFIG", "PLUGIN_DATA", "CLAUDE_PLUGIN_DATA"}}
        command = [sys.executable, "-I", "-B"]
        if ascii_stdout:
            command += ["-c", "import sys, runpy; sys.stdout.reconfigure(encoding='ascii'); path=sys.argv.pop(1); runpy.run_path(path, run_name='__main__')"]
        command += [str(ROOT / "hooks/runtime/feedback_cli.py"), *args]
        return subprocess.run(command, input=payload, capture_output=True, text=True,
                              encoding="utf-8", env=environment, check=False)

    def test_all_standalone_clients_and_non_utf8_console_export(self):
        config = self.base / "config.json"
        config.write_text(json.dumps(self.settings), encoding="utf-8")
        prompt = "Нет, ты упустил проверку русского текста."
        for client in ("claude", "codex", "gemini", "cursor"):
            result = self.run_cli("event", "--client", client, "--config", str(config),
                                  payload=json.dumps(self.event(client, prompt)))
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(bool(output), client != "cursor")
        exported = self.run_cli("export", "--state-dir", str(self.data), ascii_stdout=True)
        self.assertEqual(exported.returncode, 0, exported.stderr)
        records = [json.loads(line) for line in exported.stdout.splitlines()]
        self.assertEqual({item["source"]["client"] for item in records}, {"claude", "codex", "gemini", "cursor"})
        self.assertTrue(all(item["excerpt"] == prompt for item in records))
        cursor = {**self.event("cursor", prompt), "hook_event_name": "postToolUse", "tool_use_id": "tool-1"}
        result = self.run_cli("event", "--client", "cursor", "--config", str(config), payload=json.dumps(cursor))
        self.assertEqual(set(json.loads(result.stdout)), {"additional_context"})

    def test_cli_persistence_annotation_export_and_invalid_input(self):
        config = self.base / "config.json"
        config.write_text(json.dumps(self.settings), encoding="utf-8")
        result = self.run_cli("event", "--client", "gemini", "--config", str(config), payload=json.dumps(self.event("gemini")))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("additionalContext", json.loads(result.stdout)["hookSpecificOutput"])
        listed = self.run_cli("list", "--state-dir", str(self.data))
        key = json.loads(listed.stdout)[0]["id"]
        annotation = self.run_cli("annotate", key, "--state-dir", str(self.data), payload='{"category":"uncertain","basis":"unknown"}')
        self.assertEqual(annotation.returncode, 0, annotation.stderr)
        self.assertEqual(json.loads(annotation.stdout)["status"], "candidate")
        exported = self.run_cli("export", "--state-dir", str(self.data))
        self.assertEqual(json.loads(exported.stdout)["id"], key)
        invalid = self.run_cli("event", "--client", "gemini", "--config", str(config), payload='{"prompt":"SECRET_PAYLOAD","prompt":"duplicate"}')
        self.assertEqual(invalid.returncode, 0)
        self.assertEqual(json.loads(invalid.stdout), {})
        self.assertNotIn("SECRET_PAYLOAD", invalid.stderr)
        unknown = self.run_cli("show", "missing", "--state-dir", str(self.data))
        self.assertEqual(unknown.returncode, 2)


if __name__ == "__main__":
    unittest.main()
