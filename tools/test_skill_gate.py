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


# Claude Code relays a subagent's hand-back and another session's message as meta prompt entries.
def hand_back(sender="a6d2e4f8a0b1c3d5"):
    return {"type": "user", "isMeta": True, "origin": {"kind": "peer", "from": sender},
            "message": {"role": "user", "content": f"Another Claude session sent a message:\n<agent-message from=\"{sender}\">\n"
                        "[Subagent hand-back] The text below is the final report of a subagent this session delegated to.\n"
                        "  The parser is fixed.\n</agent-message>"}}


def session_message():
    return {"type": "user", "isMeta": True, "origin": {"kind": "peer", "from": "local_c41d"},
            "message": {"role": "user", "content": "Another Claude session sent a message: <cross-session-message "
                        "from=\"local_c41d\">Is the review finished?</cross-session-message>"}}


# Claude Code records a skill's slash command as the prompt and the skill's body as a meta entry after it.
def slash_command(name, directory="C:\\plugins\\assay\\skills\\"):
    return [{"type": "user", "message": {"role": "user", "content": (
                f"<command-message>assay:{name}</command-message>\n<command-name>/assay:{name}</command-name>\n"
                "<command-args>Fix the parser</command-args>")}},
            {"type": "user", "isMeta": True, "message": {"role": "user", "content": [
                {"type": "text", "text": f"Base directory for this skill: {directory}{name}\n\n# Title\n\nBody."}]}}]


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

    def apply(self, event):
        return skill_gate.apply({**self.base, **event}, NAMES, self.directory, clock=lambda: self.now)

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
        self.assertIn("The answer already given stands. Finding nothing to change is a normal result: a few words "
                      "in the reply's language saying the answer is unchanged", text)
        self.assertIn("Naming the skill or reference or saying the work complies gives the user nothing", text)
        self.assertIn("nothing needs changing only to show the check had an effect", text)
        self.assertIn("corrections that would change", text)
        self.assertIn("without repeating the answer or the announcement", text)
        self.assertIn("only mentioned a skill without applying it needs no load", text)
        self.assertNotIn("one short line", text)
        self.assertNotIn("starts with", text)

    def test_a_subagent_is_not_told_to_close_on_a_few_words(self):
        # What it writes next may be all its parent receives.
        text = self.feedback(self.report("Using `assay:code-change` to fix it."), "SubagentStop")
        self.assertIn("The answer already given stands: after loading, one short line is enough when nothing "
                      "changes, otherwise only the corrections that would change", text)
        self.assertNotIn("a few words", text)

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

    def test_a_negated_mention_is_no_announcement(self):
        for text in ("I did not use `assay:code-change`, a short answer was enough.",
                     "The plan was weak. Я не применял навык `assay:code-change`, так как хватило короткого ответа.",
                     "I didn't load `assay:code-change`.", "Answered without the `assay:code-change` skill.",
                     "Ответил без навыка `assay:code-change`.", "Not loaded: `assay:code-change`, `assay:test-writing`.",
                     "Не загружены: `assay:code-change` и `assay:test-writing`.",
                     "`assay:code-change` was not needed here.", "Навык `assay:code-change` здесь не нужен.",
                     "`assay:code-change` and `assay:test-writing` do not apply to a read-only review.",
                     "This is a throwaway probe, so `assay:test-writing` does not apply."):
            with self.subTest(text=text):
                self.assertEqual([], skill_gate.declared(text, NAMES))
                self.assertEqual({}, self.stop(text))

    def test_an_announcement_survives_negations_it_does_not_govern(self):
        cases = {
            "Using `assay:code-change`; I did not use `assay:test-writing`.": ["code-change"],
            "Использую `assay:code-change`, а не `assay:test-writing`.": ["code-change"],
            "Using `assay:code-change`, not `assay:test-writing`, for the parser.": ["code-change"],
            "Using `assay:code-change` without touching the public API.": ["code-change"],
            "Использую `assay:code-change` не только для правки, но и для чистки.": ["code-change"],
            "Using `assay:code-change` to fix what does not parse and `assay:test-writing` for its test.":
                ["code-change", "test-writing"],
            "Not guessing, using `assay:evidence-research` to check the claim.": ["evidence-research"],
            "Применяю навык `assay:evidence-research`: без источников вывод не проверить.": ["evidence-research"],
            "I did not guess: using `assay:evidence-research`.": ["evidence-research"],
        }
        for text, names in cases.items():
            with self.subTest(text=text):
                self.assertEqual(names, skill_gate.declared(text, NAMES))

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

    def test_a_skill_its_slash_command_expanded_is_loaded(self):
        path = self.transcript(*slash_command("code-change"), said("Using `assay:code-change` to fix the parser."),
                               RESULT)
        self.assertEqual({}, self.stop("Done.", transcript_path=path))
        # The scan's find joins the records, so the next turn needs no transcript.
        self.assertEqual({}, self.stop("Using `assay:code-change`."))
        # The same text in a tool result or a typed prompt, a command with no expansion or a subagent's
        # expansion is no load of the session's.
        command, expansion = slash_command("test-writing")
        echoed = expansion["message"]["content"][0]["text"]
        result = {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "content": echoed}, {"type": "text", "text": echoed}]}}
        cases = {"tool result": [prompt(), result], "typed": [prompt(echoed)], "unexpanded": [command],
                 "subagent": [command, {**expansion, "isSidechain": True}]}
        for case, entries in cases.items():
            with self.subTest(case=case):
                path = self.transcript(*entries, said("Using `assay:test-writing`."), name="other.jsonl")
                self.assertIn("test-writing", self.feedback(self.stop("Done.", transcript_path=path)))

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
        # Without an agent identity nothing is held.
        unloaded = {"hook_event_name": "SubagentStop", "last_assistant_message": "Using `assay:test-writing`."}
        self.assertEqual({}, self.apply(unloaded))

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
        self.assertEqual(["code-change", "test-writing"], skill_gate.loaded(event, NAMES, self.directory, **clock))
        self.assertEqual(["code-change"], skill_gate.loaded(event, {"code-change"}, self.directory, **clock))
        self.assertEqual([], skill_gate.loaded({**event, "session_id": "other"}, NAMES, self.directory, **clock))
        self.assertEqual([], skill_gate.loaded({**event, "session_id": None}, NAMES, self.directory, **clock))
        blocked = self.directory / "file"
        blocked.write_text("not a directory", encoding="utf-8")
        self.assertEqual([], skill_gate.loaded(event, NAMES, blocked, **clock))

    def test_missing_identity_and_missing_state_are_inert(self):
        stop = {"hook_event_name": "Stop", "last_assistant_message": "Using `assay:code-change`."}
        self.assertEqual({}, self.apply({**stop, "session_id": None}))
        # The runtime never reaches the gate without a place for its records.
        self.assertEqual(({}, None), process({**self.base, **stop}, "claude", {}, clock=lambda: self.now))

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

    # The owner's turn announced a skill it never loaded; its own stop already continued once.
    EARLIER = (prompt(), said("Using `assay:code-change` to fix the parser."), said("The answer is unchanged."))

    def test_a_relayed_turn_does_not_carry_the_previous_turns_announcement(self):
        bare = {key: value for key, value in hand_back().items() if key != "origin"}
        for index, opening in enumerate(([hand_back()], [session_message()], [hand_back(), hand_back("b1")], [bare])):
            with self.subTest(opening=[entry.get("origin", {}).get("kind") for entry in opening]):
                path = self.transcript(*self.EARLIER, *opening, said("The worker reports the parser fixed."),
                                       name=f"relayed{index}.jsonl")
                self.assertEqual({}, self.stop("The worker reports the parser fixed.", transcript_path=path))

    def test_a_relayed_turn_is_held_to_what_it_announces_itself(self):
        path = self.transcript(*self.EARLIER, hand_back(), said("Using `assay:test-writing` to add the test."))
        text = self.feedback(self.stop("Added.", transcript_path=path))
        self.assertIn("announces test-writing", text)
        self.assertNotIn("code-change", text)

    def test_a_message_delivered_inside_a_running_turn_keeps_the_turn(self):
        # A tool result before the relayed entry shows the turn was still running when it arrived.
        path = self.transcript(prompt(), said("Using `assay:code-change` to fix the parser."), called("ls", tool="Bash"),
                               RESULT, hand_back(), said("Done."))
        self.assertIn("announces code-change", self.feedback(self.stop("Done.", transcript_path=path)))


if __name__ == "__main__":
    unittest.main()
