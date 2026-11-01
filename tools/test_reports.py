"""Claude report check: a turn that changed code or wrote a plan carries the lines its skills ask for; no model runs."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import activation, reports
from runtime.cli import process

APP = "C:\\work\\src\\parser.py"
TESTS = "C:\\work\\tests\\test_parser.py"
PAGE = "C:\\work\\web\\Panel.vue"
PLAN = "C:\\work\\docs\\plans\\2026-10-ingest.md"
CREATED = "File created successfully at: {}"
UPDATED = "The file {} has been updated successfully."


def tool(name, data, ident):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": ident, "name": name, "input": data}]}}


def returned(ident, text="ok"):
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": ident, "content": text}]}}


def edit(path, ident="e1", text="b"):
    return [tool("Edit", {"file_path": path, "old_string": "a", "new_string": text}, ident),
            returned(ident, UPDATED.format(path))]


def write(path, ident="w1", text="x = 1\n", new=True):
    return [tool("Write", {"file_path": path, "content": text}, ident),
            returned(ident, (CREATED if new else UPDATED).format(path))]


def prompt(text="Fix the parser"):
    return {"type": "user", "message": {"role": "user", "content": text}}


class LineTests(unittest.TestCase):
    def test_labels_count_at_a_line_start_in_either_language_and_form(self):
        for text in ("Verified: unit suite — local venv — after the parser fix", "- Not verified: Linux — no runner",
                     "**Проверено:** тесты — локально — после правки", "* **Не проверено**: CI", "  __Verified__: x"):
            with self.subTest(text=text):
                self.assertTrue(reports.VERIFIED.search("Done.\n" + text))
        for text in ("I verified: the parser", "Unverified: x", "Verified that it works", "Проверено вручную"):
            with self.subTest(text=text):
                self.assertFalse(reports.VERIFIED.search(text))
        for heading in ("## What already exists", "### 2. Что уже есть", "# What already exists in the project"):
            with self.subTest(heading=heading):
                self.assertTrue(reports.EXISTING.search("# Plan\n\n" + heading + "\n- x"))
        self.assertFalse(reports.EXISTING.search("What already exists: nothing"))

    def test_a_table_row_counts_only_with_a_label_in_its_first_cell(self):
        for row in ("| Проверено | тесты | 33 из 33 |", "| Не проверено | CI | нет доступа |",
                    "| Verified | unit suite | passes |", "| **Not verified** | Linux | no runner |"):
            with self.subTest(row=row):
                self.assertTrue(reports.VERIFIED.search("Done.\n\n" + row))
        for row in ("| Статус | Проверка | Итог |", "| --- | --- | --- |", "| Проверено вручную | x |",
                    "| Тесты | Проверено |", "Проверено | тесты"):
            with self.subTest(row=row):
                self.assertFalse(reports.VERIFIED.search(row))

    def test_the_activation_list_matches_the_module(self):
        self.assertEqual(reports.RULES, activation.REPORT_RULES)
        self.assertEqual(frozenset(reports.RULES), activation.load_rules(ROOT)[0].report_rules)
        catalog = {rule["skill"].split("/", 1)[1] for rule in activation.load_rules(ROOT)[0]}
        self.assertLessEqual({row.skill for row in reports.ROWS}, catalog)

    def test_a_setting_that_disables_the_removed_reuse_row_still_loads_and_changes_nothing(self):
        self.assertNotIn("report-reuse", reports.RULES)
        self.assertEqual(activation.load_rules(ROOT), activation.load_rules(ROOT, disabled_rules=["report-reuse"]))


class StopTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def transcript(self, *entries, name="session.jsonl"):
        path = self.directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        flat = [item for entry in entries for item in (entry if isinstance(entry, list) else [entry])]
        path.write_text("".join(json.dumps(entry) + "\n" for entry in flat), encoding="utf-8")
        return str(path)

    def stop(self, *entries, last="Done.", **extra):
        return {"session_id": "s1", "hook_event_name": "Stop", "transcript_path": self.transcript(*entries),
                "last_assistant_message": last, **extra}

    def note(self, event, rules=reports.RULES, skills=None):
        result = reports.stopped(event, rules, skills)
        return result["hookSpecificOutput"]["additionalContext"] if result else ""

    def test_edited_code_without_a_verification_line_is_named(self):
        for path in (APP, TESTS, PAGE):
            with self.subTest(path=path):
                text = self.note(self.stop(prompt(), edit(path)))
                self.assertIn("this turn edited " + path.split("\\")[-1], text)
                self.assertIn("a table `Status | Check | Result`", text)
                self.assertIn("labels in the reply's language", text)
                self.assertIn("a check a call or two can run is run now", text)
                self.assertIn("tried and failed, with the error", text)
                self.assertIn("what will settle it and the record that tracks it", text)
                self.assertIn("without explaining it", text)
                # A literal English line in the note is what a Russian reply copied.
                self.assertNotIn("`Verified:", text)
                self.assertNotIn("C:\\work", text)
        text = self.note(self.stop(prompt(), edit(APP), edit(TESTS, "e2"), edit(APP, "e3")))
        self.assertIn("edited parser.py, test_parser.py and", text)

    def test_a_shell_edit_is_seen_through_the_files_the_turn_stages(self):
        shell = ("cd web && python - <<'EOF'\nopen('static/styles.css','w').write('x')\nEOF\n; "
                 "git add web/static/styles.css docs/notes.md; git commit -q -m 'fix(web): x'")
        text = self.note(self.stop(prompt(), tool("Bash", {"command": shell}, "b1"), returned("b1")))
        self.assertIn("this turn edited styles.css and", text)
        for command in ("git add docs/guide.md README.md", "git -C repo add -A src tests", "git status src/app.py",
                        "echo git add src/app.py.bak"):
            with self.subTest(command=command):
                self.assertEqual("", self.note(self.stop(prompt(), tool("PowerShell", {"command": command}, "b1"),
                                                         returned("b1"))))
        self.assertIn("app.py", self.note(self.stop(prompt(), tool("PowerShell", {
            "command": "git -C C:/work add -A src/app.py; git -C C:/work commit -m x"}, "b1"), returned("b1"))))

    def test_a_verification_line_or_no_code_edit_keeps_it_silent(self):
        self.assertEqual("", self.note(self.stop(prompt(), edit(APP), last="Fixed.\nVerified: suite — venv — after fix")))
        self.assertEqual("", self.note(self.stop(prompt(), edit(APP), last="Не проверено: CI — нет доступа")))
        table = "Fixed.\n\n| Статус | Проверка | Итог |\n| --- | --- | --- |\n| Проверено | тесты | проходят |"
        self.assertEqual("", self.note(self.stop(prompt(), edit(APP), last=table)))
        self.assertIn("parser.py", self.note(self.stop(prompt(), edit(APP), last="| Статус | Итог |\n| --- | --- |")))
        for path in ("C:\\work\\docs\\guide.md", "C:\\work\\tmp\\probe.py", "C:\\work\\config.yaml",
                     "C:\\work\\.private\\x\\parse.py"):
            with self.subTest(path=path):
                self.assertEqual("", self.note(self.stop(prompt(), edit(path))))
        self.assertEqual("", self.note(self.stop(prompt(), tool("Read", {"file_path": APP}, "r1"), returned("r1"))))

    def test_only_this_turn_counts(self):
        self.assertEqual("", self.note(self.stop(prompt(), edit(APP), prompt("Thanks, now explain"))))
        compacted = [{"type": "system", "subtype": "compact_boundary"},
                     {"type": "user", "isCompactSummary": True, "message": {"role": "user", "content": "Summary"}}]
        self.assertEqual("", self.note(self.stop(prompt(), edit(APP), *compacted)))
        # A task notification starts a turn too; edits before it belong to the earlier one.
        notification = {"type": "user", "message": {"role": "user", "content": "<task-notification> done"}}
        self.assertEqual("", self.note(self.stop(prompt(), edit(APP), notification)))

    def test_the_report_waits_for_a_background_task_of_the_turn(self):
        def finished(*names):
            tags = "".join(f"<task-id>{name}</task-id>\n" for name in names)
            return {"type": "user", "message": {"role": "user", "content": f"<task-notification>\n{tags}<status>completed</status>"}}
        command = [tool("Bash", {"command": "gate", "run_in_background": True}, "b1"),
                   returned("b1", "Command running in background with ID: task1. Output is being written to: x")]
        agent = [tool("Agent", {"description": "build: alfi — parser"}, "a1"),
                 returned("a1", "Async agent launched successfully. (Internal metadata.) agentId: worker1 (internal ID)")]
        # Still running: the final message is still to come.
        self.assertEqual("", self.note(self.stop(prompt(), edit(APP), command, last="The gate runs in the background.")))
        self.assertEqual("", self.note(self.stop(prompt(), edit(APP), agent, last="The worker is running.")))
        # Finished: the edit before the notification is asked for, so the wait loses nothing.
        self.assertIn("parser.py", self.note(self.stop(prompt(), edit(APP), command, finished("task1"))))
        self.assertIn("parser.py", self.note(self.stop(prompt(), edit(APP), agent, finished("worker1"))))
        by_call = {"type": "user", "message": {"role": "user", "content": "<task-notification>\n<tool-use-id>b1</tool-use-id>"}}
        self.assertIn("parser.py", self.note(self.stop(prompt(), edit(APP), command, by_call)))
        queued = {"type": "attachment", "attachment": {"type": "queued_command", "prompt": "<task-notification><task-id>task1</task-id>"}}
        self.assertIn("parser.py", self.note(self.stop(prompt(), edit(APP), command, queued)))
        # One of two still running keeps it waiting; a report after the wait settles it.
        self.assertEqual("", self.note(self.stop(prompt(), edit(APP), command, agent, finished("task1"), last="One to go.")))
        self.assertEqual("", self.note(self.stop(prompt(), edit(APP), command, finished("task1"), last="Verified: gate — passed")))

    def test_only_a_running_launch_of_this_turn_makes_the_report_wait(self):
        command = [tool("Bash", {"command": "gate", "run_in_background": True}, "b1"),
                   returned("b1", "Command running in background with ID: task1.")]
        refused = [tool("Bash", {"command": "gate", "run_in_background": True}, "b1"),
                   {"type": "user", "message": {"role": "user", "content": [
                       {"type": "tool_result", "tool_use_id": "b1", "is_error": True, "content": "not run"}]}}]
        self.assertIn("parser.py", self.note(self.stop(prompt(), edit(APP), refused)))
        self.assertIn("parser.py", self.note(self.stop(prompt("first"), command, prompt(), edit(APP))))
        # A subagent that stops is finishing: its report is due now.
        event = {"session_id": "s1", "hook_event_name": "SubagentStop", "agent_id": "w1", "last_assistant_message": "Done.",
                 "agent_transcript_path": self.transcript(prompt("packet"), edit(APP), command)}
        self.assertIn("parser.py", self.note(event))
        # A plan is asked for whatever runs in the background.
        self.assertIn("2026-10-ingest.md", self.note(self.stop(prompt(), write(PLAN, text="# Plan"), command)))
        # A relayed message before any launch still starts a turn.
        other = {"type": "user", "message": {"role": "user", "content": "<task-notification><task-id>old</task-id>"}}
        done = {"type": "user", "message": {"role": "user", "content": "<task-notification><task-id>task1</task-id>"}}
        self.assertEqual("", self.note(self.stop(prompt(), edit(APP), other, command, done)))

    def test_an_edit_already_reported_in_the_turn_is_not_asked_for_again(self):
        def said(text):
            return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}
        # Shapes from a live session: a hand-back is a meta user entry, a notification a queued attachment.
        hand_back = {"type": "user", "isMeta": True, "message": {"role": "user", "content": [
            {"type": "text", "text": "Another Claude session sent a message:\n<agent-message from=\"a1\">done"}]}}
        queued = {"type": "attachment", "attachment": {"type": "queued_command", "prompt": "<task-notification>x"}}
        reported = said("Fixed.\n- Проверено: suite — venv — after the fix")
        self.assertEqual("", self.note(self.stop(prompt(), edit(APP), reported, hand_back, queued, last="Waiting.")))
        # An edit after the report is asked for, and only that one.
        text = self.note(self.stop(prompt(), edit(APP), reported, hand_back, edit(TESTS, "e2"), last="Done."))
        self.assertIn("this turn edited test_parser.py and", text)
        self.assertNotIn("parser.py, ", text)
        # Without a report the edit before the relayed messages is still asked for.
        self.assertIn("parser.py", self.note(self.stop(prompt(), edit(APP), hand_back, queued, last="Waiting.")))
        # A table in an earlier message of the turn reports the edit too.
        tabled = said("| Статус | Проверка | Итог |\n| --- | --- | --- |\n| Проверено | тесты | проходят |")
        self.assertEqual("", self.note(self.stop(prompt(), edit(APP), tabled, hand_back, last="Waiting.")))

    def test_a_new_source_file_asks_only_for_the_verification_line(self):
        # The hook cannot see whether a reuse decision was taken, so a new file adds no reuse demand.
        text = self.note(self.stop(prompt(), write(APP)))
        self.assertIn("this turn edited parser.py", text)
        self.assertNotIn("created", text)
        self.assertNotIn("Reuse", text)
        self.assertEqual("", self.note(self.stop(prompt(), write(APP), last="Verified: suite — after the new parser")))

    def test_a_plan_without_the_existing_section_is_named(self):
        text = self.note(self.stop(prompt("Plan the ingest"), write(PLAN, text="# Plan\n\n## Units\n- U1")))
        self.assertIn("implementation-planning: this turn wrote 2026-10-ingest.md", text)
        self.assertIn("for a plan, add the section to the plan file", text)
        for entries in ([write(PLAN, text="# Plan\n\n## What already exists\n- none\n")],
                        [write(PLAN, text="# План\n\n## 1. Что уже есть\n- ничего\n")],
                        [write(PLAN, text="# Plan\n"), edit(PLAN, "e9", text="## What already exists\n- x\n")],
                        [edit(PLAN)], [write("C:\\work\\docs\\explanation.md", text="# Notes")]):
            with self.subTest(entries=entries):
                self.assertEqual("", self.note(self.stop(prompt("Plan the ingest"), *entries)))
        # A later rewrite without the section brings the note back.
        self.assertIn("2026-10-ingest.md", self.note(self.stop(
            prompt(), write(PLAN, text="## What already exists\n- x"), write(PLAN, "w2", text="# Plan v2"))))

    def test_all_missing_lines_come_in_one_note(self):
        text = self.note(self.stop(prompt(), write(APP), write(PLAN, "w2", text="# Plan")))
        self.assertTrue(text.startswith("Assay report check:"))
        self.assertEqual(2, text.count("\n- "))

    def test_rules_skills_a_second_stop_and_a_subagent(self):
        event = self.stop(prompt(), write(APP))
        self.assertEqual("", self.note(event, rules=("plan-existing",)))
        self.assertIn("edited parser.py", self.note(event, rules=("report-verification",)))
        self.assertEqual("", self.note(event, skills={"implementation-planning"}))
        self.assertEqual("", self.note({**event, "stop_hook_active": True}))
        self.assertEqual("", self.note({**event, "last_assistant_message": None}))
        self.assertEqual("", self.note({**event, "transcript_path": str(self.directory / "missing.jsonl")}))
        worker = [{**entry, "isSidechain": True} for entry in [prompt("Packet"), *edit(APP)]]
        sub = {"session_id": "s1", "hook_event_name": "SubagentStop", "agent_id": "a1", "last_assistant_message": "Done.",
               "agent_transcript_path": self.transcript(*worker, name="agent-a1.jsonl")}
        self.assertIn("this subagent", self.note(sub))
        self.assertEqual("", self.note({**sub, "agent_id": None}))
        # The root agent does not count a worker's edits that appear in its own file as sidechain entries.
        self.assertEqual("", self.note(self.stop(prompt(), *worker)))

    def test_the_runtime_returns_the_note_and_the_rule_turns_it_off(self):
        data = self.directory / "data"
        event = self.stop(prompt(), edit(APP))
        result, error = process(event, "claude", {"CLAUDE_PLUGIN_DATA": str(data)})
        self.assertIsNone(error)
        self.assertIn("Assay report check", result["hookSpecificOutput"]["additionalContext"])
        config = self.directory / "hooks.json"
        config.write_text(json.dumps({"disabled_rules": ["report-verification"], "state_dir": str(data)}), encoding="utf-8")
        self.assertEqual(({}, None), process(event, "claude", {"ASSAY_HOOK_CONFIG": str(config)}))
        # A configuration written for the removed reuse row keeps working and keeps the verification row.
        config.write_text(json.dumps({"disabled_rules": ["report-reuse"], "state_dir": str(data)}), encoding="utf-8")
        result, error = process(event, "claude", {"ASSAY_HOOK_CONFIG": str(config)})
        self.assertIsNone(error)
        self.assertIn("Assay report check", result["hookSpecificOutput"]["additionalContext"])
        self.assertNotIn("report check", json.dumps(process(event, "codex", {"CLAUDE_PLUGIN_DATA": str(data)})[0]))


if __name__ == "__main__":
    unittest.main()
