"""The line a person sees when a stop check continues a Claude turn, beside a note that stays as it was; no model runs."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import branches, reports, skill_gate, sources
from runtime.cli import process
from test_branch_check import CLAIM_EN, load
from test_reports import edit, write
from test_source_checks import prompt, read, said

APP = "C:\\work\\src\\parser.py"
PAGE = "C:\\app\\src\\App.vue"
ANNOUNCED = "Using `assay:code-change`.\n\nDone."
READ_CLAIM = "I read researcher.py in full."
FAMILIES = ("skill gate", "read-claim check", "skill branch check", "report check")
MAX_LINE = 80


def cases():
    """Each family's firing turn: the checks expected in the line, the transcript and the final message."""
    partial = read("r1", 1, 200, 900, limit=200)
    return {
        "gate": (("skill gate",), [prompt(), said(ANNOUNCED)], ANNOUNCED),
        "read claim": (("read-claim check",), [prompt(), *partial, said(READ_CLAIM)], READ_CLAIM),
        "branch": (("skill branch check",), [prompt(), *load(), said(CLAIM_EN)], ""),
        "report": (("report check",), [prompt(), *edit(APP)], "Done."),
        "branch and report": (("skill branch check", "report check"),
                              [prompt(), *load("assay:code-change"), *write(PAGE), said("Done.")], ""),
        "read claim and report": (("read-claim check", "report check"),
                                  [prompt(), *partial, *edit(APP), said(READ_CLAIM)], READ_CLAIM),
        # The gate goes first and takes the whole continuation.
        "gate over read claim": (("skill gate",), [prompt(), *partial, said(ANNOUNCED + "\n" + READ_CLAIM)],
                                 ANNOUNCED + "\n" + READ_CLAIM),
    }


def stop_event(directory, entries, last, **extra):
    path = Path(directory) / "session.jsonl"
    path.write_text("".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries), encoding="utf-8")
    return {"session_id": "session", "cwd": "work", "hook_event_name": "Stop", "transcript_path": str(path),
            "last_assistant_message": last, **extra}


class StopLineTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.data = self.directory / "data"
        self.environment = {"CLAUDE_PLUGIN_DATA": str(self.data)}

    def note(self, check, event):
        """The note as the check that owns it writes it, read past the runtime that adds the line."""
        written = {"skill gate": lambda: skill_gate.apply(event, {"code-change"}, self.data),
                   "read-claim check": lambda: sources.stopped(event),
                   "skill branch check": lambda: branches.stopped(event),
                   "report check": lambda: reports.stopped(event)}[check]()
        return written["hookSpecificOutput"]["additionalContext"]

    def assert_line(self, line, checks):
        self.assertTrue(line.startswith("Assay: "), line)
        self.assertNotIn("\n", line)
        self.assertLessEqual(len(line), MAX_LINE)
        for family in FAMILIES:
            (self.assertIn if family in checks else self.assertNotIn)(family, line)

    def test_each_family_carries_its_line_beside_the_unchanged_note(self):
        for name, (checks, entries, last) in cases().items():
            with self.subTest(name):
                # The gate remembers a load per session, so each case is its own.
                event = stop_event(self.directory, entries, last, session_id=name)
                result, error = process(event, "claude", self.environment)
                self.assertIsNone(error)
                self.assertEqual({"hookSpecificOutput", "systemMessage"}, set(result))
                self.assert_line(result["systemMessage"], checks)
                self.assertEqual({"hookEventName": "Stop",
                                  "additionalContext": "\n\n".join(self.note(check, event) for check in checks)},
                                 result["hookSpecificOutput"])
                # Nothing in the note names the line, so it cannot reach the model through it.
                self.assertNotIn(result["systemMessage"], result["hookSpecificOutput"]["additionalContext"])

    def test_a_subagent_stop_that_continues_carries_the_line_too(self):
        checks, entries, last = cases()["report"]
        path = self.directory / "agent-a1.jsonl"
        path.write_text("".join(json.dumps({**entry, "isSidechain": True}) + "\n" for entry in entries), encoding="utf-8")
        event = {"session_id": "session", "cwd": "work", "hook_event_name": "SubagentStop", "agent_id": "a1",
                 "agent_transcript_path": str(path), "last_assistant_message": last}
        result, error = process(event, "claude", self.environment)
        self.assertIsNone(error)
        self.assert_line(result["systemMessage"], checks)
        self.assertEqual("SubagentStop", result["hookSpecificOutput"]["hookEventName"])
        self.assertEqual(self.note("report check", event), result["hookSpecificOutput"]["additionalContext"])

    def test_no_continuation_means_no_line(self):
        quiet = stop_event(self.directory, [prompt(), said("Nothing to report.")], "Nothing to report.")
        self.assertEqual(({}, None), process(quiet, "claude", self.environment))
        for name, (_, entries, last) in cases().items():
            with self.subTest(name):
                # The turn a check already continued ends without another word from it.
                event = stop_event(self.directory, entries, last, stop_hook_active=True)
                self.assertEqual(({}, None), process(event, "claude", self.environment))

    def test_codex_output_does_not_change(self):
        for name, (_, entries, last) in cases().items():
            with self.subTest(name):
                event = stop_event(self.directory, entries, last)
                self.assertEqual(({}, None), process(event, "codex", self.environment))
        manifest = json.loads((ROOT / "hooks/codex.json").read_text(encoding="utf-8"))["hooks"]
        self.assertNotIn("Stop", manifest)
        self.assertNotIn("SubagentStop", manifest)

    def test_the_printed_reply_holds_the_note_and_the_line_in_one_object(self):
        checks, entries, last = cases()["report"]
        event = stop_event(self.directory, entries, last)
        environment = {key: value for key, value in os.environ.items() if key != "ASSAY_HOOK_CONFIG"}
        done = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "hooks/runtime/cli.py"), "--client", "claude"],
                              input=json.dumps(event).encode(), capture_output=True, check=True, timeout=60,
                              env={**environment, **self.environment})
        reply = json.loads(done.stdout)
        self.assert_line(reply["systemMessage"], checks)
        self.assertEqual(self.note("report check", event), reply["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
