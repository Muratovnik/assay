"""Owner configuration must not be resolved relative to an arbitrary project."""
from __future__ import annotations

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
from runtime import cli


class HookOptionsTests(unittest.TestCase):
    def test_relative_config_is_rejected_before_reading_project_files(self):
        for location in ("hooks.json", "../hooks.json"):
            with self.subTest(location=location), patch.object(cli, "read_json") as read:
                with self.assertRaisesRegex(ValueError, "absolute"):
                    cli.options({"ASSAY_HOOK_CONFIG": location})
                read.assert_not_called()

    def test_explicit_absolute_config_remains_supported(self):
        location = str(ROOT / "owner-hook-config.json")
        with patch.object(cli, "read_json", return_value={"skill_note_form": "note"}) as read:
            settings = cli.options({"ASSAY_HOOK_CONFIG": location})
        read.assert_called_once_with(location)
        self.assertEqual("note", settings["skill_note_form"])
        self.assertIsNone(settings["state_dir"])

    def test_removed_feedback_options_are_refused_with_their_names(self):
        location = str(ROOT / "owner-hook-config.json")
        removed = {"record_events": True, "feedback_capture": "metadata", "feedback_trigger": "explicit"}
        for raw in (removed, {"record_events": False}, {**removed, "unknown": 1, "skill_note_form": "note"}):
            with self.subTest(raw=sorted(raw)), patch.object(cli, "read_json", return_value=raw):
                with self.assertRaises(cli.RemovedOptions) as caught:
                    cli.options({"ASSAY_HOOK_CONFIG": location})
            message = str(caught.exception)
            for name in removed:
                self.assertEqual(name in raw, name in message)
        with patch.object(cli, "read_json", return_value={"unknown": 1}):
            with self.assertRaisesRegex(ValueError, "unknown hook option") as caught:
                cli.options({"ASSAY_HOOK_CONFIG": location})
            self.assertNotIsInstance(caught.exception, cli.RemovedOptions)

    def test_removed_option_message_reaches_the_hook_diagnostic_and_doctor(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "hooks.json"
            config.write_text(json.dumps({"record_events": True, "feedback_capture": "off"}), encoding="utf-8")
            environment = {"ASSAY_HOOK_CONFIG": str(config)}
            event = {"hook_event_name": "UserPromptSubmit", "session_id": "s", "cwd": temporary,
                     "turn_id": "t", "prompt": "hello"}
            result, error = cli.process(event, "codex", environment)
            self.assertEqual({}, result)
            self.assertIn("feedback_capture, record_events", error)
            with self.assertRaises(cli.RemovedOptions):
                cli.doctor("codex", environment)
            with patch.dict(os.environ, environment), patch("sys.stderr", io.StringIO()) as stderr:
                self.assertEqual(2, cli.main(["doctor", "--client", "codex"]))
            self.assertIn("feedback_capture, record_events", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
