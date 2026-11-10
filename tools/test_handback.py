"""Claude hand-back hold: a subagent's report meets the stop checks before it is delivered; no model runs."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import activation, handback, reports
from runtime.cli import process

APP = "C:\\work\\src\\parser.py"
UPDATED = "The file {} has been updated successfully."
REPORT = "Fixed the parser so empty input returns an empty list."
VERIFIED = REPORT + "\nVerified: unit suite — local venv — after the parser fix"


def tool(name, data, ident):
    return {"type": "assistant", "isSidechain": True,
            "message": {"content": [{"type": "tool_use", "id": ident, "name": name, "input": data}]}}


def returned(ident, text="ok", error=False):
    return {"type": "user", "isSidechain": True, "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": ident, "content": text, **({"is_error": True} if error else {})}]}}


def packet(text="Fix the parser and report through your tools."):
    return {"type": "user", "isSidechain": True, "message": {"role": "user", "content": text}}


def edited():
    return [tool("Edit", {"file_path": APP, "old_string": "a", "new_string": "b"}, "e1"), returned("e1", UPDATED.format(APP))]


def said(text):
    return {"type": "assistant", "isSidechain": True, "message": {"content": [{"type": "text", "text": text}]}}


def launched(ident="b1", task="task1"):
    """A gate started in the background, as Claude Code 2.1.317 answers it."""
    return [tool("Bash", {"command": "python tools/check.py --all", "run_in_background": True}, ident),
            returned(ident, f"Command running in background with ID: {task}. Output is being written to: x")]


def notified(ident="b1", task="task1"):
    """The task notification that resumes a subagent, in the shape its transcript records."""
    return {"type": "user", "isSidechain": True, "isMeta": True, "origin": {"kind": "task-notification"},
            "message": {"role": "user", "content": (
                "[SYSTEM NOTIFICATION - NOT USER INPUT]\nThis is an automated background-task event.\n"
                f"<task-notification>\n<task-id>{task}</task-id>\n<tool-use-id>{ident}</tool-use-id>\n"
                "<status>completed</status>\n<summary>Background command completed (exit code 0)</summary>\n"
                "</task-notification>")}}


class HoldTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.data = self.directory / "data"
        self.session = self.directory / "s1.jsonl"
        self.session.write_text("", encoding="utf-8")

    def worker(self, *entries):
        """The subagent's own transcript, where Claude Code keeps it beside the session's."""
        path = self.directory / "s1" / "subagents" / "agent-a1.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        flat = [item for entry in entries for item in (entry if isinstance(entry, list) else [entry])]
        path.write_text("".join(json.dumps(entry) + "\n" for entry in flat), encoding="utf-8")
        return str(path)

    def handing_back(self, message=REPORT, prompt="p1", **extra):
        # The shape a live Claude Code 2.1.304 subagent sent: no agent_transcript_path, the session's transcript_path.
        return {"session_id": "s1", "hook_event_name": "PreToolUse", "tool_name": "SubagentHandback",
                "tool_input": {"message": message}, "agent_id": "a1", "agent_type": "general-purpose",
                "prompt_id": prompt, "transcript_path": str(self.session), **extra}

    def stopping(self, last="Done."):
        return {"session_id": "s1", "hook_event_name": "SubagentStop", "agent_id": "a1",
                "agent_type": "general-purpose", "last_assistant_message": last,
                "agent_transcript_path": str(self.directory / "s1" / "subagents" / "agent-a1.jsonl")}

    def run_hook(self, event, client="claude", **environment):
        result, error = process(event, client, {"CLAUDE_PLUGIN_DATA": str(self.data), **environment})
        self.assertIsNone(error)
        return result

    def test_the_first_hand_back_the_stop_checks_object_to_is_refused_and_the_retry_passes(self):
        self.worker(packet(), *edited())
        result = self.run_hook(self.handing_back())["hookSpecificOutput"]
        self.assertEqual("deny", result["permissionDecision"])
        reason = result["permissionDecisionReason"]
        self.assertTrue(reason.startswith("Assay held this hand-back once, so the report has not reached the parent"))
        self.assertIn("Assay report check", reason)
        self.assertIn("this turn edited parser.py", reason)
        # The check's own advice is for a delivered answer; the report must go out whole.
        self.assertIn("its advice not to repeat the answer does not apply here", reason)
        self.assertIn("call SubagentHandback again with the complete report, not only the added lines", reason)
        self.assertIn("That call goes through.", reason)
        # The retry is never refused, even when the report still lacks the line.
        self.assertEqual({}, self.run_hook(self.handing_back()))
        # A new request of the same subagent gets its own check.
        self.assertEqual("deny", self.run_hook(self.handing_back(prompt="p2"))["hookSpecificOutput"]["permissionDecision"])

    def test_a_report_that_carries_the_line_passes_at_once(self):
        self.worker(packet(), *edited())
        self.assertEqual({}, self.run_hook(self.handing_back(VERIFIED)))

    def test_an_announced_skill_the_subagent_did_not_load_is_held_by_the_gate(self):
        self.worker(packet(), tool("Read", {"file_path": APP}, "r1"), returned("r1"))
        reason = self.run_hook(self.handing_back("Used `assay:code-change` to review the parser.\nAll good."))[
            "hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Assay skill gate: this turn announces code-change", reason)
        # A report of a few closing words would pass the retry and leave the parent with nothing.
        self.assertNotIn("a few words", reason)
        loaded = [packet(), tool("Skill", {"skill": "assay:code-change"}, "k1"), returned("k1")]
        self.worker(*loaded)
        self.assertEqual({}, self.run_hook(self.handing_back("Used `assay:code-change`.\nAll good.", prompt="p3")))

    def test_nothing_is_refused_without_a_place_for_the_key_or_with_the_rule_off(self):
        self.worker(packet(), *edited())
        event = self.handing_back()
        # Without the data directory a refusal could repeat and lose the report.
        self.assertEqual(({}, None), process(event, "claude", {}))
        config = self.directory / "hooks.json"
        config.write_text(json.dumps({"disabled_rules": ["handback-hold"], "state_dir": str(self.data)}), encoding="utf-8")
        self.assertEqual(({}, None), process(event, "claude", {"ASSAY_HOOK_CONFIG": str(config)}))
        self.assertEqual({}, self.run_hook(event, client="codex"))
        # The main session does not hand back; a call without a report is not checked.
        self.assertEqual({}, self.run_hook({**event, "agent_id": None}))
        self.assertEqual({}, self.run_hook({**event, "tool_input": {}}))

    def test_after_a_delivered_hand_back_the_stop_stays_silent(self):
        self.worker(packet(), *edited(), tool("SubagentHandback", {"message": REPORT}, "h1"), returned("h1", "Delivered."))
        self.assertEqual({}, self.run_hook(self.stopping()))

    def test_after_a_refused_hand_back_the_stop_still_speaks(self):
        self.worker(packet(), *edited(), tool("SubagentHandback", {"message": REPORT}, "h1"),
                    returned("h1", "Assay held this hand-back once", error=True))
        text = self.run_hook(self.stopping())["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Assay report check", text)
        # So does a subagent that has not handed back, as before.
        self.worker(packet(), *edited())
        self.assertIn("Assay report check", self.run_hook(self.stopping())["hookSpecificOutput"]["additionalContext"])
        # A hand-back in an earlier turn of the same subagent does not silence this one.
        self.worker(packet(), tool("SubagentHandback", {"message": REPORT}, "h0"), returned("h0", "Delivered."),
                    packet("One more fix, please."), *edited())
        self.assertIn("Assay report check", self.run_hook(self.stopping())["hookSpecificOutput"]["additionalContext"])

    def test_a_subagent_waiting_on_its_own_background_run_is_checked_only_at_its_final_stop(self):
        # The turn edits code, announces a skill it never loaded and claims a partial read in full,
        # so a final stop has feedback from the gate, the source check and the report check.
        work = [packet(), tool("Read", {"file_path": APP, "limit": 2}, "r1"), returned("r1", "1\ta\n2\tb\n"),
                *edited(), said("Using `assay:code-change` for the parser.\n\nI read parser.py in full.")]
        self.worker(*work, *launched(), said("The gate runs in the background; I end the turn until it reports."))
        self.assertEqual({}, self.run_hook(self.stopping("The gate runs in the background.")))
        # A second wait in the same turn, on a new launch after the first reported, is not checked either.
        self.worker(*work, *launched(), notified(), *launched("b2", "task2"), said("Rerunning the gate."))
        self.assertEqual({}, self.run_hook(self.stopping("Rerunning the gate.")))
        # Once every launch has reported, the stop is final and checked as before.
        self.worker(packet(), *edited(), *launched(), said("Waiting for the gate."), notified(), said(REPORT))
        text = self.run_hook(self.stopping(REPORT))["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Assay report check", text)
        self.assertIn("this turn edited parser.py", text)
        # A launch the client refused never ran, so it leaves nothing to wait for.
        self.worker(packet(), *edited(), tool("Bash", {"command": "gate", "run_in_background": True}, "b1"),
                    returned("b1", "Permission denied", error=True), said(REPORT))
        self.assertIn("Assay report check", self.run_hook(self.stopping(REPORT))["hookSpecificOutput"]["additionalContext"])

    def test_a_hand_back_during_the_wait_is_still_held(self):
        self.worker(packet(), *edited(), *launched())
        self.assertEqual({}, self.run_hook(self.stopping("Waiting for the gate.")))
        # The hand-back is the subagent's answer, whatever still runs.
        self.assertEqual("deny", self.run_hook(self.handing_back())["hookSpecificOutput"]["permissionDecision"])

    def test_a_wait_the_hook_cannot_recognise_is_checked_as_a_final_stop(self):
        self.worker(packet(), *edited(), *launched(), said("Waiting for the gate."))
        self.assertEqual({}, self.run_hook(self.stopping("Waiting for the gate.")))
        # A Monitor is not a launch the hook recognises, so the stop counts as final.
        monitor = [tool("Monitor", {"command": "tail -f log", "timeout_ms": 270000}, "m1"),
                   returned("m1", "Monitor started (task m1, expires in 4m 30s unless the source ends first).")]
        self.worker(packet(), *edited(), *monitor, said("Watching the log."))
        text = self.run_hook(self.stopping("Watching the log."))["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Assay report check", text)
        # A transcript that cannot be read shows no wait either.
        self.assertFalse(reports.waiting({**self.stopping(), "agent_transcript_path": str(self.directory / "none.jsonl")}))

    def checked(self, last=REPORT):
        """The feedback of a stop that must be checked as final."""
        result = self.run_hook(self.stopping(last))
        self.assertIn("hookSpecificOutput", result, "the stop was not checked")
        return result["hookSpecificOutput"]["additionalContext"]

    def test_a_stopped_launch_ends_the_wait(self):
        stopped = [tool("TaskStop", {"task_id": "task1"}, "s1"),
                   returned("s1", '{"message":"Successfully stopped task: task1 (python tools/check.py --all)"}')]
        self.worker(packet(), *edited(), *launched(), *stopped, said(REPORT))
        self.assertIn("Assay report check", self.checked())
        killed = [tool("KillShell", {"shell_id": "task1"}, "s1"), returned("s1", "Shell task1 killed")]
        self.worker(packet(), *edited(), *launched(), *killed, said(REPORT))
        self.assertIn("Assay report check", self.checked())
        # A stop the client refused stopped nothing, so the subagent still waits.
        refused = [tool("TaskStop", {"task_id": "task1"}, "s1"),
                   returned("s1", "<tool_use_error>No task found with ID: task1.</tool_use_error>", error=True)]
        self.worker(packet(), *edited(), *launched(), *refused, said("Waiting for the gate."))
        self.assertEqual({}, self.run_hook(self.stopping("Waiting for the gate.")))

    def test_only_launches_of_the_current_packet_keep_a_stop_unchecked(self):
        message = {"type": "user", "isSidechain": True, "isMeta": True, "origin": {"kind": "coordinator"},
                   "message": {"role": "user", "content": "The coordinator sent a message while you were working:\n"
                               "Repair the parser as well.\n\nAddress this before completing your current task."}}
        # The earlier packet's launch never reported; the next packet's report is final all the same.
        self.worker(packet(), *launched(), said("Waiting."), message, *edited(), said(REPORT))
        self.assertIn("Assay report check", self.checked())
        # A launch of the current packet still makes its stop a wait.
        self.worker(packet(), *launched(), said("Waiting."), message, *edited(), *launched("b2", "task2"), said("Waiting."))
        self.assertEqual({}, self.run_hook(self.stopping("Waiting.")))

    def test_an_id_that_is_not_a_string_leaves_the_stop_checked_as_final(self):
        for ident in (["b1"], {"id": "b1"}):
            with self.subTest(ident=ident):
                broken = [tool("Bash", {"command": "gate", "run_in_background": True}, ident),
                          returned(ident, "Command running in background with ID: task1.")]
                self.worker(packet(), *edited(), *broken, said(REPORT))
                self.assertIn("Assay report check", self.checked())

    def test_a_command_the_client_moved_to_the_background_is_a_launch(self):
        # The client's two wordings, at the start of the result and after the output the command printed.
        for result in ("Command was moved to the background (ID: bmv7q2k1x) after running for 180s. "
                       "Output is being written to: C:/tmp/bmv7q2k1x.output",
                       "Command did not complete within its 120s timeout and was moved to the background "
                       "(ID: bmv7q2k1x). Output is being written to: C:/tmp/bmv7q2k1x.output",
                       "collected 856 items\n\nCommand was moved to the background (ID: bmv7q2k1x) after running "
                       "for 180s. Output is being written to: C:/tmp/bmv7q2k1x.output"):
            with self.subTest(result=result[:40]):
                moved = [tool("Bash", {"command": "python -m unittest"}, "b1"), returned("b1", result)]
                self.worker(packet(), *edited(), *moved, said("Waiting for the suite."))
                self.assertEqual({}, self.run_hook(self.stopping("Waiting for the suite.")))
        # It ends like any launch: by its notification, or by a stop that names the id the client gave it.
        ended = [notified("b1", "bmv7q2k1x"), said(REPORT)]
        self.worker(packet(), *edited(), *moved, *ended)
        self.assertIn("Assay report check", self.checked())
        stopped = [tool("TaskStop", {"task_id": "bmv7q2k1x"}, "s1"), returned("s1", '{"message":"Successfully stopped"}')]
        self.worker(packet(), *edited(), *moved, *stopped, said(REPORT))
        self.assertIn("Assay report check", self.checked())

    def test_the_hold_refuses_with_the_note_and_shows_the_person_nothing(self):
        self.worker(packet(), *edited())
        event = self.handing_back()
        note = reports.stopped(handback.stop_event(event))["hookSpecificOutput"]["additionalContext"]
        result = self.run_hook(event)
        # The retry delivers the report, so no reply is left for a line to explain.
        self.assertEqual({"hookSpecificOutput"}, set(result))
        self.assertIn("\n" + note + "\n", result["hookSpecificOutput"]["permissionDecisionReason"])

    def test_a_stop_after_a_refused_hand_back_shows_the_line(self):
        self.worker(packet(), *edited(), tool("SubagentHandback", {"message": REPORT}, "h1"),
                    returned("h1", "Assay held this hand-back once", error=True))
        self.assertIn("report check", self.run_hook(self.stopping())["systemMessage"])

    def test_the_rule_and_the_manifest(self):
        self.assertTrue(activation.load_rules(ROOT)[0].handback_hold)
        self.assertFalse(activation.load_rules(ROOT, disabled_rules=["handback-hold"])[0].handback_hold)
        groups = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
        own = [group for group in groups if group["matcher"] == "^SubagentHandback$"]
        self.assertEqual(15, own[0]["hooks"][0]["timeout"])
        self.assertNotIn("onFailure", own[0]["hooks"][0])
        # Exactly one group answers a hand-back.
        import re
        self.assertEqual(1, sum(bool(re.search(group["matcher"], "SubagentHandback")) for group in groups))
        self.assertFalse(handback.handing_back({"hook_event_name": "PreToolUse", "tool_name": "Read", "agent_id": "a1",
                                                "tool_input": {"message": "x"}}))


if __name__ == "__main__":
    unittest.main()
