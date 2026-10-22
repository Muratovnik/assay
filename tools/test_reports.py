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
        self.assertTrue(reports.REUSE.search("Reuse: not applicable — project-specific parsing"))
        self.assertTrue(reports.REUSE.search("- **Переиспользование:** нет готового"))
        self.assertFalse(reports.REUSE.search("We reuse: nothing"))
        for heading in ("## What already exists", "### 2. Что уже есть", "# What already exists in the project"):
            with self.subTest(heading=heading):
                self.assertTrue(reports.EXISTING.search("# Plan\n\n" + heading + "\n- x"))
        self.assertFalse(reports.EXISTING.search("What already exists: nothing"))

    def test_the_activation_list_matches_the_module(self):
        self.assertEqual(reports.RULES, activation.REPORT_RULES)
        self.assertEqual(frozenset(reports.RULES), activation.load_rules(ROOT)[0].report_rules)
        catalog = {rule["skill"].split("/", 1)[1] for rule in activation.load_rules(ROOT)[0]}
        self.assertLessEqual({row.skill for row in reports.ROWS}, catalog)


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
                self.assertIn("`Verified: <check> — <environment> — after <change>`", text)
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
        # A reuse line covers a new file the same way, and a verification line does not.
        self.assertEqual("", self.note(self.stop(prompt(), write(APP), said("Verified: x — y — z\nReuse: none — w"),
                                                 hand_back, last="Waiting.")))
        self.assertIn("created parser.py", self.note(self.stop(prompt(), write(APP), said("Verified: x — y — z"),
                                                               hand_back, last="Waiting.")))

    def test_a_new_source_file_without_a_reuse_line_is_named(self):
        text = self.note(self.stop(prompt(), write(APP)))
        self.assertIn("this turn created parser.py", text)
        self.assertIn("`Reuse: not applicable — <why>`", text)
        self.assertEqual("", self.note(self.stop(prompt(), write(APP), last=(
            "Verified: suite — venv — after the new parser\nReuse: own code — gap: none fits; alternatives checked: x"))))
        # Overwriting a file, creating a test or a scratch script is not a new source file.
        for entries in (write(APP, new=False), write(TESTS), write("C:\\work\\tmp\\probe.py"),
                        [tool("Write", {"file_path": APP, "content": "x"}, "w1"),
                         {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "is_error": True,
                          "tool_use_id": "w1", "content": CREATED.format(APP)}]}}]):
            with self.subTest(entries=entries[1]):
                self.assertNotIn("created", self.note(self.stop(prompt(), entries, last="Verified: x — y — after z")))

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
        self.assertEqual(3, text.count("\n- "))

    def test_rules_skills_a_second_stop_and_a_subagent(self):
        event = self.stop(prompt(), write(APP))
        self.assertEqual("", self.note(event, rules=("plan-existing",)))
        self.assertNotIn("Reuse", self.note(event, rules=("report-verification",)))
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
        self.assertNotIn("report check", json.dumps(process(event, "codex", {"CLAUDE_PLUGIN_DATA": str(data)})[0]))


if __name__ == "__main__":
    unittest.main()
