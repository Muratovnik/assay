"""Claude skill gate: a turn that announces an unloaded skill continues once; no model runs."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import skill_gate
from runtime.cli import process

NAMES = {"evidence-research", "code-change", "test-writing"}
BOUNDARY = {"type": "system", "subtype": "compact_boundary"}
SUMMARY = {"type": "user", "isCompactSummary": True, "isVisibleInTranscriptOnly": True,
           "message": {"role": "user", "content": "This session is being continued from a previous conversation."}}
RESULT = {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "ok"}]}}


def prompt(text="Fix the parser"):
    return {"type": "user", "message": {"role": "user", "content": text}}


def said(text, **extra):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}, **extra}


def called(skill, tool="Skill", **extra):
    data = {"skill": skill} if tool == "Skill" else {"file_path": skill} if tool == "Read" else {"message": skill}
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": tool, "input": data}]}, **extra}


def reattached(*names):
    return {"type": "attachment", "attachment": {"type": "invoked_skills", "skills": [
        {"name": "assay:" + name, "path": "plugin:assay:" + name, "content": "..."} for name in names]}}


class SkillGateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.now = 1000.0
        self.base = {"session_id": "session", "cwd": "work"}

    def apply(self, event, client="claude", directory=None):
        return skill_gate.apply({**self.base, **event}, client, NAMES,
                                self.directory if directory is None else directory, clock=lambda: self.now)

    def stop(self, text, **extra):
        return self.apply({"hook_event_name": "Stop", "last_assistant_message": text, **extra})

    def load(self, tool, data, **extra):
        return self.apply({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": data, **extra})

    def transcript(self, *entries, name="session.jsonl"):
        path = self.directory / name
        path.write_text("".join(json.dumps(entry) + "\n" for entry in entries), encoding="utf-8")
        return str(path)

    def feedback(self, result, event="Stop"):
        """The continuation text, once it is checked to be stop feedback rather than a block."""
        self.assertNotIn("decision", result)
        output = result["hookSpecificOutput"]
        self.assertEqual({"hookEventName", "additionalContext"}, set(output))
        self.assertEqual(event, output["hookEventName"])
        return output["additionalContext"]

    def report(self, text, agent="worker", **extra):
        return self.apply({"hook_event_name": "SubagentStop", "agent_id": agent, "agent_type": "general-purpose",
                           "last_assistant_message": text, **extra})

    def test_an_announced_but_unloaded_skill_continues_the_turn_once(self):
        text = self.feedback(self.stop("Using `assay:evidence-research` to check the facts.\n\nFrom memory: /usage."))
        self.assertIn("announces evidence-research", text)
        self.assertIn("has not loaded", text)
        self.assertEqual({}, self.stop("Using `assay:evidence-research`.\n\nStill unloaded.", stop_hook_active=True))

    def test_the_continuation_keeps_the_answer_instead_of_asking_for_it_again(self):
        text = self.feedback(self.stop("Using `assay:code-change` to fix it."))
        self.assertIn("The answer already given stands: after loading, one short line is enough when nothing "
                      "changes, otherwise only the corrections that would change", text)
        self.assertIn("without repeating the answer or the announcement", text)
        self.assertNotIn("starts with", text)

    def test_announcements_name_skills_in_code_spans_or_on_the_legacy_line(self):
        cases = {
            "Использую `assay:code-change` и `assay:test-writing` для правки и тестов.": ["code-change", "test-writing"],
            "Using `assay:code-change``assay:test-writing` together.": ["code-change", "test-writing"],
            "**Using** `assay:evidence-research`, then `assay:evidence-research` again.": ["evidence-research"],
            "Assay: code-change, test-writing": ["code-change", "test-writing"],
            "**Assay:** evidence-research (already loaded)": ["evidence-research"],
        }
        for text, names in cases.items():
            with self.subTest(text=text):
                self.assertEqual(names, skill_gate.declared(text, NAMES))

    def test_none_mentions_unknown_names_and_later_lines_announce_nothing(self):
        for text in ("Assay: none", "Assay: none. Nothing here needs a method.", "Assay: plugin-authoring",
                     "Just the answer.", "", None, "Intro first.\nAssay: code-change",
                     "Intro first.\nUsing `assay:code-change`.", "The gate reads `code-change` now.",
                     "Using `assay:plugin-authoring` here.", "Skipping test-writing: nothing to test.",
                     "Using assay:code-change without code spans."):
            with self.subTest(text=text):
                self.assertEqual([], skill_gate.declared(text, NAMES))
                self.assertEqual({}, self.stop(text))

    def test_skill_tool_or_skill_file_read_satisfies_the_gate(self):
        self.assertEqual({}, self.load("Skill", {"skill": "assay:evidence-research"}))
        self.assertEqual({}, self.stop("Using `assay:evidence-research`."))
        self.load("Read", {"file_path": "C:\\plugins\\assay\\skills\\code-change\\SKILL.md"})
        self.assertEqual({}, self.stop("**Assay:** code-change, evidence-research (already loaded)"))

    def test_only_the_missing_skill_is_named_in_the_reason(self):
        self.load("Skill", {"skill": "code-change"})
        text = self.feedback(self.stop("Using `assay:code-change` and `assay:test-writing`."))
        self.assertIn("test-writing", text)
        self.assertNotIn("code-change", text)

    def test_other_tools_and_other_skills_are_not_loads(self):
        self.load("Skill", {"skill": "plugin-authoring"})
        self.load("Read", {"file_path": "/plugins/assay/skills/code-change/references/reuse.md"})
        self.load("Grep", {"pattern": "skills/code-change/SKILL.md"})
        self.assertIn("code-change", self.feedback(self.stop("Assay: code-change")))

    def test_an_earlier_message_of_the_turn_carries_the_announcement(self):
        path = self.transcript(prompt(), said("Использую `assay:code-change` для правки парсера."), RESULT,
                               said("Проверяю тесты."), RESULT)
        self.assertIn("announces code-change", self.feedback(self.stop("Готово.", transcript_path=path)))
        loaded = self.transcript(prompt(), said("Using `assay:code-change` to fix the parser."),
                                 called("assay:code-change"), RESULT, name="loaded.jsonl")
        self.assertEqual({}, self.stop("Done.", transcript_path=loaded))

    def test_a_previous_turn_announcement_is_not_held_again(self):
        path = self.transcript(prompt(), said("Using `assay:code-change` to fix it."), prompt("And now?"))
        self.assertEqual({}, self.stop("Still fixed.", transcript_path=path))
        # Reading past the turn's start for loads does not pick up its old announcements.
        path = self.transcript(prompt(), said("Using `assay:test-writing` for tests."), called("assay:code-change"),
                               prompt("Next"), said("Using `assay:code-change` to finish."), name="earlier.jsonl")
        self.assertEqual({}, self.stop("Done.", transcript_path=path))
        # A tool result or a compaction summary does not start a turn.
        path = self.transcript(prompt(), said("Using `assay:test-writing`."), RESULT, SUMMARY, name="tail.jsonl")
        self.assertIn("test-writing", self.feedback(self.stop("Done.", transcript_path=path)))

    def test_a_new_session_id_finds_loads_in_its_transcript(self):
        # A continued, resumed or forked session gets a new id and empty records.
        copied = {"sessionId": "old-session"}
        path = self.transcript(prompt(), called("assay:evidence-research", **copied),
                               called("C:\\x\\skills\\code-change\\SKILL.md", tool="Read", **copied), prompt())
        self.assertEqual({}, self.stop("Using `assay:evidence-research` and `assay:code-change`.",
                                       transcript_path=path))
        # The scan's finds join the records, so the next turn needs no transcript.
        self.assertEqual({}, self.stop("Using `assay:code-change`."))

    def test_compaction_keeps_only_the_skills_it_reattached(self):
        path = self.transcript(prompt(), called("assay:code-change"), called("assay:test-writing"), BOUNDARY,
                               SUMMARY, reattached("code-change"), prompt())
        text = self.feedback(self.stop("Using `assay:code-change` and `assay:test-writing`.", transcript_path=path))
        self.assertIn("announces test-writing", text)
        self.assertNotIn("code-change", text)

    def test_a_subagent_entry_in_the_main_transcript_is_not_a_root_load(self):
        path = self.transcript(prompt(), called("assay:code-change", isSidechain=True), prompt())
        self.assertIn("code-change", self.feedback(self.stop("Using `assay:code-change`.", transcript_path=path)))

    def test_an_unreadable_transcript_leaves_the_records_in_charge(self):
        garbage = self.directory / "garbage.jsonl"
        garbage.write_bytes(b"\x00not json\n{\"type\": \n")
        for path in (str(self.directory / "missing.jsonl"), str(garbage), 42, "", str(self.directory)):
            with self.subTest(path=path):
                self.assertIn("code-change", self.feedback(self.stop("Using `assay:code-change`.",
                                                                     transcript_path=path)))

    def test_the_scan_reads_only_a_bounded_tail(self):
        path = self.transcript(called("assay:code-change"), said("x" * 600), prompt())
        with patch.object(skill_gate, "MAX_TRANSCRIPT", 400), patch.object(skill_gate, "BLOCK", 64):
            self.assertIn("code-change", self.feedback(self.stop("Using `assay:code-change`.",
                                                                 transcript_path=path)))
        with patch.object(skill_gate, "BLOCK", 64):
            self.assertEqual({}, self.stop("Using `assay:code-change`.", transcript_path=path))

    def test_a_subagent_or_another_session_cannot_satisfy_the_root(self):
        self.load("Skill", {"skill": "evidence-research"}, agent_id="worker")
        self.assertIn("evidence-research", self.feedback(self.stop("Assay: evidence-research")))
        self.load("Skill", {"skill": "evidence-research"}, session_id="other")
        self.assertIn("evidence-research", self.feedback(self.stop("Assay: evidence-research")))

    def test_a_subagent_report_is_held_to_the_skills_that_subagent_loaded(self):
        text = self.feedback(self.report("Using `assay:code-change`.\n\nPatched."), "SubagentStop")
        self.assertIn("announces code-change", text)
        self.assertIn("this subagent has not loaded", text)
        self.assertEqual({}, self.report("Using `assay:code-change`.", stop_hook_active=True))
        # The root's load or another worker's does not count for this worker.
        self.load("Skill", {"skill": "code-change"})
        self.load("Skill", {"skill": "code-change"}, agent_id="other")
        self.assertIn("code-change", self.feedback(self.report("Assay: code-change"), "SubagentStop"))
        self.load("Read", {"file_path": "C:\\plugins\\assay\\skills\\code-change\\SKILL.md"}, agent_id="worker")
        self.assertEqual({}, self.report("Using `assay:code-change`."))
        self.assertEqual({}, self.report("Assay: none"))
        # Without an agent identity, or in Codex, nothing is held.
        unloaded = {"hook_event_name": "SubagentStop", "last_assistant_message": "Using `assay:test-writing`."}
        self.assertEqual({}, self.apply(unloaded))
        self.assertEqual({}, self.apply({**unloaded, "agent_id": "worker"}, client="codex"))

    def test_a_subagent_is_read_from_its_own_transcript(self):
        packet = prompt("Patch the parser and report.")
        announced = said("Using `assay:test-writing` to cover the parser.", isSidechain=True)
        own = self.transcript(packet, announced, RESULT, name="agent.jsonl")
        text = self.feedback(self.report("Done.", agent_transcript_path=own), "SubagentStop")
        self.assertIn("announces test-writing", text)
        # Its own load counts; the main transcript is not where a worker's load lives.
        main = self.transcript(prompt(), called("assay:test-writing"), name="main.jsonl")
        loaded = self.transcript(packet, announced, called("assay:test-writing", isSidechain=True),
                                 name="agent-loaded.jsonl")
        self.assertEqual({}, self.report("Done.", agent="w2", transcript_path=main, agent_transcript_path=loaded))
        handback = self.transcript(packet, called("Using `assay:evidence-research`.\n\nFindings.",
                                                  tool="SubagentHandback", isSidechain=True), name="handback.jsonl")
        text = self.feedback(self.report("", agent="w3", agent_transcript_path=handback), "SubagentStop")
        self.assertIn("announces evidence-research", text)

    def test_loads_expire_unless_used(self):
        self.load("Skill", {"skill": "code-change"})
        self.now += skill_gate.TTL - 10
        self.assertEqual({}, self.stop("Using `assay:code-change`."))  # Use slides the expiry.
        self.now += 20
        self.assertEqual({}, self.stop("Using `assay:code-change`."))
        self.now += skill_gate.TTL + 1
        self.assertIn("code-change", self.feedback(self.stop("Using `assay:code-change`.")))

    def test_loaded_reports_the_records_without_ever_raising(self):
        self.load("Skill", {"skill": "code-change"})
        self.load("Skill", {"skill": "assay:test-writing"})
        event = {**self.base, "hook_event_name": "UserPromptSubmit"}
        clock = {"clock": lambda: self.now}
        self.assertEqual(["code-change", "test-writing"], skill_gate.loaded(event, "claude", NAMES, self.directory, **clock))
        self.assertEqual(["code-change"], skill_gate.loaded(event, "claude", {"code-change"}, self.directory, **clock))
        self.assertEqual([], skill_gate.loaded(event, "codex", NAMES, self.directory, **clock))
        self.assertEqual([], skill_gate.loaded({**event, "session_id": "other"}, "claude", NAMES, self.directory, **clock))
        self.assertEqual([], skill_gate.loaded({**event, "session_id": None}, "claude", NAMES, self.directory, **clock))
        self.assertEqual([], skill_gate.loaded(event, "claude", NAMES, "", **clock))
        blocked = self.directory / "file"
        blocked.write_text("not a directory", encoding="utf-8")
        self.assertEqual([], skill_gate.loaded(event, "claude", NAMES, blocked, **clock))

    def test_codex_missing_identity_and_missing_state_are_inert(self):
        stop = {"hook_event_name": "Stop", "last_assistant_message": "Using `assay:code-change`."}
        self.assertEqual({}, self.apply(stop, client="codex"))
        self.assertEqual({}, self.apply({**stop, "session_id": None}))
        self.assertEqual({}, self.apply(stop, directory=""))

    def test_runtime_continues_claude_stops_and_honours_the_setting(self):
        environment = {"CLAUDE_PLUGIN_DATA": str(self.directory / "data")}
        stop = {"hook_event_name": "Stop", "session_id": "session", "cwd": "work",
                "last_assistant_message": "Using `assay:code-change`.\n\nDone."}
        result, error = process(stop, "claude", environment, clock=lambda: self.now)
        self.assertIsNone(error)
        self.assertIn("code-change", self.feedback(result))
        process({"hook_event_name": "PreToolUse", "session_id": "session", "cwd": "work", "tool_name": "Skill",
                 "tool_input": {"skill": "assay:code-change"}}, "claude", environment, clock=lambda: self.now)
        self.assertEqual({}, process(stop, "claude", environment, clock=lambda: self.now)[0])
        unloaded = {**stop, "last_assistant_message": "Using `assay:test-writing`."}
        self.assertEqual({}, process(unloaded, "codex", environment, clock=lambda: self.now)[0])
        settings = self.directory / "settings.json"
        settings.write_text(json.dumps({"disabled_rules": ["skill-gate"]}), encoding="utf-8")
        result, _ = process(unloaded, "claude", {**environment, "ASSAY_HOOK_CONFIG": str(settings)},
                            clock=lambda: self.now)
        self.assertEqual({}, result)

    def test_runtime_check_names_what_this_session_already_loaded(self):
        environment = {"CLAUDE_PLUGIN_DATA": str(self.directory / "data")}
        prompt_event = {"hook_event_name": "UserPromptSubmit", "session_id": "session", "cwd": "work",
                        "prompt": "Fix the parser"}

        def check(event=prompt_event, client="claude"):
            result, error = process(event, client, environment, clock=lambda: self.now)
            self.assertIsNone(error)
            return result["hookSpecificOutput"]["additionalContext"]

        self.assertNotIn("Already loaded", check())
        process({"hook_event_name": "PreToolUse", "session_id": "session", "cwd": "work", "tool_name": "Skill",
                 "tool_input": {"skill": "assay:code-change"}}, "claude", environment, clock=lambda: self.now)
        self.assertIn("Already loaded in this session: code-change.", check())
        self.assertNotIn("Already loaded", check({**prompt_event, "session_id": "other"}))
        self.assertNotIn("Already loaded", check(client="codex"))
        # A bare "continue" restores the previous suggestion with the same hint.
        self.assertIn("Already loaded in this session: code-change.", check({**prompt_event, "prompt": "continue"}))

    def test_runtime_gives_a_subagent_the_check_and_holds_its_report(self):
        environment = {"CLAUDE_PLUGIN_DATA": str(self.directory / "data")}
        worker = {"session_id": "session", "cwd": "work", "agent_id": "worker", "agent_type": "general-purpose"}
        for client in ("claude", "codex"):
            with self.subTest(client=client):
                result, error = process({**worker, "hook_event_name": "SubagentStart"}, client, environment,
                                        clock=lambda: self.now)
                self.assertIsNone(error)
                output = result["hookSpecificOutput"]
                self.assertEqual("SubagentStart", output["hookEventName"])
                self.assertIn("Assay skill check for this subagent", output["additionalContext"])
        report = {**worker, "hook_event_name": "SubagentStop",
                  "last_assistant_message": "Using `assay:code-change`."}
        result, error = process(report, "claude", environment, clock=lambda: self.now)
        self.assertIsNone(error)
        self.assertIn("this subagent", self.feedback(result, "SubagentStop"))
        process({**worker, "hook_event_name": "PreToolUse", "tool_name": "Skill",
                 "tool_input": {"skill": "assay:code-change"}}, "claude", environment, clock=lambda: self.now)
        self.assertEqual({}, process(report, "claude", environment, clock=lambda: self.now)[0])

    def test_only_the_claude_manifest_registers_stop(self):
        claude = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))["hooks"]
        codex = json.loads((ROOT / "hooks/codex.json").read_text(encoding="utf-8"))["hooks"]
        self.assertIn("Stop", claude)
        self.assertNotIn("Stop", codex)


if __name__ == "__main__":
    unittest.main()
