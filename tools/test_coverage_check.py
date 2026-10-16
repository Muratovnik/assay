"""Claude coverage check: an absence claim made after loading evidence-research without its coverage reference continues once; no model runs."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import coverage
from runtime.cli import process

REFERENCE = "C:\\agent\\.claude\\plugins\\cache\\assay\\assay\\0.25.0\\skills\\evidence-research\\references\\search-and-coverage.md"
OTHER = "C:\\agent\\.claude\\plugins\\cache\\assay\\assay\\0.25.0\\skills\\evidence-research\\references\\evidence-and-claims.md"
CLAIM_RU = "Ни один из найденных навыков не делает того, что вы описали; поведения «пример ≠ граница» нет нигде."
CLAIM_EN = "There are no existing skills that challenge an idea this way."


def prompt(text="Are there skills that push back on an idea?"):
    return {"type": "user", "message": {"role": "user", "content": text}}


def said(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def tool(name, data, ident):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": ident, "name": name, "input": data}]}}


def returned(ident, text="ok"):
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": ident, "content": text}]}}


def load(skill="assay:evidence-research", ident="s1"):
    return [tool("Skill", {"skill": skill}, ident), returned(ident, "Launching skill")]


def read(path=REFERENCE, ident="r1"):
    return [tool("Read", {"file_path": path}, ident), returned(ident, "1\t# Search and coverage\n")]


class CoverageCheckTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.base = {"session_id": "session", "cwd": "work"}

    def transcript(self, *entries, name="session.jsonl"):
        path = self.directory / name
        flat = [item for entry in entries for item in (entry if isinstance(entry, list) else [entry])]
        path.write_text("".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in flat), encoding="utf-8")
        return str(path)

    def stop(self, *entries, last="", **extra):
        return coverage.stopped({**self.base, "hook_event_name": "Stop", "transcript_path": self.transcript(*entries),
                                 "last_assistant_message": last, **extra})

    def feedback(self, result, event="Stop"):
        self.assertNotIn("decision", result)
        output = result["hookSpecificOutput"]
        self.assertEqual({"hookEventName", "additionalContext"}, set(output))
        self.assertEqual(event, output["hookEventName"])
        return output["additionalContext"]

    def test_an_absence_claim_without_the_reference_continues_the_turn(self):
        text = self.feedback(self.stop(prompt(), load(), said(CLAIM_RU)))
        self.assertIn("search-and-coverage.md", text)
        self.assertIn("нет нигде", text)  # The claim is quoted so the agent can find it.
        self.assertIn("The answer already given stands", text)
        self.assertIn("Assay coverage check", text)

    def test_reading_the_reference_in_this_context_silences_the_check(self):
        self.assertEqual({}, self.stop(prompt(), load(), read(), said(CLAIM_RU)))
        # A read in an earlier turn of the same context still counts.
        self.assertEqual({}, self.stop(prompt("first"), load(), read(), said("ok"), prompt(), said(CLAIM_EN)))
        # Printing it with a shell command counts as reading it.
        shell = [tool("Bash", {"command": f"cat '{REFERENCE}'"}, "b1"), returned("b1")]
        self.assertEqual({}, self.stop(prompt(), load(), shell, said(CLAIM_EN)))

    def test_another_reference_of_the_skill_does_not_count(self):
        self.feedback(self.stop(prompt(), load(), read(OTHER), said(CLAIM_EN)))

    def test_a_turn_that_never_loaded_the_skill_is_not_held_to_it(self):
        self.assertEqual({}, self.stop(prompt(), said(CLAIM_EN)))
        self.assertEqual({}, self.stop(prompt(), load("assay:code-change"), said(CLAIM_EN)))

    def test_loading_by_reading_skill_md_counts(self):
        skill = "C:\\x\\skills\\evidence-research\\SKILL.md"
        self.feedback(self.stop(prompt(), read(skill, "r0"), said(CLAIM_EN)))

    def test_lines_that_claim_no_absence_stay_silent(self):
        for line in ("Found three candidates: the-fool, grilling and brainstorming.",
                     "Нашёл три навыка, каждый закрывает часть требований.",
                     "There is no need to search further: one official page settles it.",
                     "No changes were needed in the hook."):
            with self.subTest(line=line):
                self.assertEqual({}, self.stop(prompt(), load(), said(line)))

    def test_absence_wordings_in_both_languages_are_recognized(self):
        for line in ("None of them covers the example-as-scope behavior.",
                     "Nothing like this exists for Codex yet.",
                     "Such a skill doesn't exist.",
                     "I'm not aware of any maintained alternative.",
                     "Готового решения нет.",
                     "Такого навыка не существует.",
                     "Ничего подобного я не нашёл."):
            with self.subTest(line=line):
                self.feedback(self.stop(prompt(), load(), said(line)))

    def test_a_claim_from_an_earlier_turn_or_a_load_before_compaction_is_not_counted(self):
        self.assertEqual({}, self.stop(prompt("first"), load(), said(CLAIM_EN), prompt(), said("Done.")))
        boundary = {"type": "system", "subtype": "compact_boundary"}
        self.assertEqual({}, self.stop(load(), boundary, prompt(), said(CLAIM_EN)))

    def test_skills_reattached_by_compaction_count_as_loaded_but_not_their_reads(self):
        boundary = {"type": "system", "subtype": "compact_boundary"}
        kept = {"type": "attachment", "attachment": {"type": "invoked_skills",
                                                     "skills": [{"name": "assay:evidence-research"}]}}
        self.feedback(self.stop(load(), read(), boundary, kept, prompt(), said(CLAIM_EN)))

    def test_the_final_message_is_checked_even_before_the_transcript_holds_it(self):
        text = self.feedback(self.stop(prompt("first"), load(), said("ok"), prompt(), said("Looking."), last=CLAIM_EN))
        self.assertIn("no existing skills", text)

    def test_a_continuation_or_an_unreadable_transcript_stays_silent(self):
        self.assertEqual({}, self.stop(prompt(), load(), said(CLAIM_EN), stop_hook_active=True))
        event = {**self.base, "hook_event_name": "Stop", "transcript_path": str(self.directory / "missing.jsonl"),
                 "last_assistant_message": CLAIM_EN}
        self.assertEqual({}, coverage.stopped(event))

    def test_a_subagent_report_is_held_to_the_skill_that_subagent_loaded(self):
        report = tool("SubagentHandback", {"message": "Report.\nNone of the candidates fits all four needs."}, "h1")
        path = self.transcript(prompt("packet"), load(), report, name="agent.jsonl")
        event = {**self.base, "hook_event_name": "SubagentStop", "agent_id": "worker",
                 "agent_transcript_path": path, "last_assistant_message": ""}
        self.assertIn("None of the candidates", self.feedback(coverage.stopped(event), "SubagentStop"))
        # The parent's load does not reach a worker that never loaded the skill.
        event["agent_transcript_path"] = self.transcript(prompt("packet"), report, name="agent2.jsonl")
        self.assertEqual({}, coverage.stopped(event))

    def test_at_most_two_claims_are_quoted(self):
        text = self.feedback(self.stop(prompt(), load(), said("Nowhere.\nNone of them.\nНигде нет.")))
        self.assertEqual(2, text.count("\u201c"))


class CoverageCheckRuntimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.environment = {"CLAUDE_PLUGIN_DATA": str(self.directory / "data")}

    def configured(self, **options):
        path = self.directory / "hooks.json"
        path.write_text(json.dumps({**options, "state_dir": str(self.directory / "data")}), encoding="utf-8")
        return {"ASSAY_HOOK_CONFIG": str(path)}

    def stop_event(self, *entries):
        path = self.directory / "session.jsonl"
        flat = [item for entry in entries for item in (entry if isinstance(entry, list) else [entry])]
        path.write_text("".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in flat), encoding="utf-8")
        return {"session_id": "session", "cwd": "work", "hook_event_name": "Stop", "transcript_path": str(path),
                "last_assistant_message": ""}

    def test_the_runtime_returns_the_note_and_its_rule_turns_it_off(self):
        stop = self.stop_event(prompt(), load(), said(CLAIM_EN))
        result, error = process(stop, "claude", self.environment)
        self.assertIsNone(error)
        self.assertIn("Assay coverage check", result["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(({}, None), process(stop, "claude", self.configured(disabled_rules=["coverage-claims"])))
        self.assertEqual(({}, None), process(stop, "codex", self.environment))

    def test_a_contradicted_read_claim_goes_first(self):
        source = "C:\\work\\src\\researcher.py"
        partial = [tool("Read", {"file_path": source, "limit": 200}, "r9"),
                   {"type": "user", "toolUseResult": {"type": "text", "file": {
                       "filePath": source, "content": "...", "startLine": 1, "numLines": 200, "totalLines": 900}},
                    "message": {"role": "user", "content": [
                        {"type": "tool_result", "tool_use_id": "r9", "content": "1\tline\n"}]}}]
        stop = self.stop_event(prompt(), load(), partial, said("I read researcher.py in full. " + CLAIM_EN))
        text = process(stop, "claude", self.environment)[0]["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Assay source check", text)
        environment = self.configured(disabled_rules=["read-claims"])
        text = process(stop, "claude", environment)[0]["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Assay coverage check", text)


if __name__ == "__main__":
    unittest.main()
