"""Claude branch check: a turn whose own actions meet a loaded skill's reading condition, without that reference read, continues once; no model runs."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import activation, branches
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


class TranscriptCase(unittest.TestCase):
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
        return branches.stopped({**self.base, "hook_event_name": "Stop", "transcript_path": self.transcript(*entries),
                                 "last_assistant_message": last, **extra})

    def feedback(self, result, event="Stop"):
        self.assertNotIn("decision", result)
        output = result["hookSpecificOutput"]
        self.assertEqual({"hookEventName", "additionalContext"}, set(output))
        self.assertEqual(event, output["hookEventName"])
        return output["additionalContext"]


class CoverageCheckTests(TranscriptCase):
    def test_an_absence_claim_without_the_reference_continues_the_turn(self):
        text = self.feedback(self.stop(prompt(), load(), said(CLAIM_RU)))
        self.assertIn("search-and-coverage.md", text)
        self.assertIn("нет нигде", text)  # The claim is quoted so the agent can find it.
        self.assertIn("The answer already given stands", text)
        self.assertIn("Assay branch check", text)

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
                     "No changes were needed in the hook.",
                     # Facts about the work, not about what exists elsewhere.
                     "The filter selects no test, so none of them ran.",
                     "Эти файлы нигде не закоммичены.",
                     "Запуск прошёл, но ни одного обобщения не получилось.",
                     "The cache file doesn't exist yet."):
            with self.subTest(line=line):
                self.assertEqual({}, self.stop(prompt(), load(), said(line)))

    def test_absence_wordings_in_both_languages_are_recognized(self):
        for line in ("None of the candidates covers the example-as-scope behavior.",
                     "There is no maintained library for this format.",
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
        self.assertEqual({}, branches.stopped(event))

    def test_a_subagent_report_is_held_to_the_skill_that_subagent_loaded(self):
        report = tool("SubagentHandback", {"message": "Report.\nNone of the candidates fits all four needs."}, "h1")
        path = self.transcript(prompt("packet"), load(), report, name="agent.jsonl")
        event = {**self.base, "hook_event_name": "SubagentStop", "agent_id": "worker",
                 "agent_transcript_path": path, "last_assistant_message": ""}
        self.assertIn("None of the candidates", self.feedback(branches.stopped(event), "SubagentStop"))
        # The parent's load does not reach a worker that never loaded the skill.
        event["agent_transcript_path"] = self.transcript(prompt("packet"), report, name="agent2.jsonl")
        self.assertEqual({}, branches.stopped(event))

    def test_at_most_two_claims_are_quoted(self):
        text = self.feedback(self.stop(prompt(), load(), said("Such a tool exists nowhere.\nNone of these skills fits.\nНигде нет такого плагина.")))
        self.assertEqual(2, text.count("\u201c"))


SKILLS = "C:\\agent\\.claude\\plugins\\cache\\assay\\assay\\0.25.0\\skills\\"
RUSSIAN = "Этот раздел объясняет, как включить проверку веток навыков и что делать, когда она срабатывает."


def reference(skill, name):
    return f"{SKILLS}{skill}\\references\\{name}"


def write(path, content="text", ident="w1", kind="Write"):
    data = ({"file_path": path, "content": content} if kind == "Write"
            else {"file_path": path, "old_string": "old", "new_string": content})
    return [tool(kind, data, ident), returned(ident)]


def launch(description, agent="general-purpose", ident="a1"):
    return [tool("Agent", {"description": description, "subagent_type": agent, "prompt": "packet"}, ident),
            returned(ident, "report")]


class BranchTableTests(TranscriptCase):
    def test_the_activation_list_matches_the_table(self):
        self.assertEqual(branches.RULES, activation.BRANCH_RULES)
        self.assertEqual(len(branches.RULES), len(set(branches.RULES)))

    def test_every_row_names_references_the_skill_ships(self):
        for row in branches.BRANCHES:
            for name in row.references:
                with self.subTest(rule=row.rule, reference=name):
                    self.assertTrue((ROOT / "skills" / row.skill / "references" / name).is_file())

    def test_a_vue_edit_calls_for_vue_structure(self):
        text = self.feedback(self.stop(prompt(), load("assay:code-change"),
                                       write("C:\\app\\src\\App.vue", kind="Edit"), said("Done.")))
        self.assertIn("code-change: references/vue-structure.md", text)
        self.assertIn("(App.vue)", text)
        self.assertNotIn("ui-delivery", text)  # Not loaded, so not held to its references.
        self.assertIn("Assay branch check", text)
        self.assertIn("The answer already given stands", text)
        # Control: a TypeScript edit, and a turn that read the reference.
        self.assertEqual({}, self.stop(prompt(), load("assay:code-change"),
                                       write("C:\\app\\src\\store.ts", kind="Edit"), said("Done.")))
        self.assertEqual({}, self.stop(prompt(), load("assay:code-change"),
                                       read(reference("code-change", "vue-structure.md")),
                                       write("C:\\app\\src\\App.vue"), said("Done.")))

    def test_check_configuration_and_moves_call_for_effective_quality_checks(self):
        signals = (write("C:\\repo\\ruff.toml"),
                   write("C:\\repo\\.github\\workflows\\ci.yml", kind="Edit"),
                   write("C:\\repo\\pyproject.toml", "[tool.ruff]\nline-length = 100\n", kind="Edit"),
                   [tool("Bash", {"command": "git mv src/a.py src/core/a.py"}, "b1"), returned("b1")])
        for signal in signals:
            with self.subTest(signal=signal[0]["message"]["content"][0]["input"]):
                text = self.feedback(self.stop(prompt(), load("assay:code-change"), signal, said("Done.")))
                self.assertIn("references/effective-quality-checks.md", text)
        # Control: a manifest edit without a tool section, and a shell read of the reference.
        self.assertEqual({}, self.stop(prompt(), load("assay:code-change"),
                                       write("C:\\repo\\pyproject.toml", 'version = "1.2.0"', kind="Edit"),
                                       said("Done.")))
        command = f"Get-Content '{reference('code-change', 'effective-quality-checks.md')}'"
        shell = [tool("PowerShell", {"command": command}, "b2"), returned("b2")]
        self.assertEqual({}, self.stop(prompt(), load("assay:code-change"), shell,
                                       write("C:\\repo\\ruff.toml"), said("Done.")))

    def test_a_review_launch_calls_for_bounded_review(self):
        for agent in (launch("review: web app quality"), launch("Check the diff", "assay:evidence-reviewer"),
                      launch("Аудит документации")):
            with self.subTest(agent=agent[0]["message"]["content"][0]["input"]["description"]):
                text = self.feedback(self.stop(prompt(), load("assay:independent-audit"), agent, said("Done.")))
                self.assertIn("independent-audit: references/bounded-review.md", text)
        # Control: a worker that repairs what a review found is not audit delegation.
        for description in ("code: apply the agreed fixes", "Fix confirmed web review findings",
                            "Map game-system coverage gaps"):
            with self.subTest(description=description):
                self.assertEqual({}, self.stop(prompt(), load("assay:independent-audit"), launch(description),
                                               said("Done.")))

    def test_writing_a_plan_calls_for_implementation_units(self):
        for path in ("C:\\repo\\docs\\plans\\2026-10-16-hook.md", "C:\\repo\\PLAN.md",
                     "C:\\agent\\.claude\\plans\\quiet-otter.md", "C:\\repo\\release-plan.md"):
            with self.subTest(path=path):
                text = self.feedback(self.stop(prompt(), load("assay:implementation-planning"), write(path),
                                               said("Plan written.")))
                self.assertIn("references/implementation-units.md", text)
        # Control: ticking a step in an existing plan, and a name that only contains "plan" inside a word.
        self.assertEqual({}, self.stop(prompt(), load("assay:implementation-planning"),
                                       write("C:\\repo\\docs\\plans\\2026-10-16-hook.md", "- [x] step", kind="Edit"),
                                       said("Done.")))
        self.assertEqual({}, self.stop(prompt(), load("assay:implementation-planning"),
                                       write("C:\\repo\\docs\\explanation.md"), said("Done.")))

    def test_an_interface_edit_calls_for_both_acceptance_references(self):
        text = self.feedback(self.stop(prompt(), load("assay:ui-delivery"),
                                       write("C:\\app\\src\\Panel.tsx", kind="Edit"), said("Done.")))
        self.assertIn("references/scenario-testing.md and references/visual-judgment.md", text)
        # A read of one leaves only the other.
        text = self.feedback(self.stop(prompt(), load("assay:ui-delivery"),
                                       read(reference("ui-delivery", "scenario-testing.md")),
                                       write("C:\\app\\src\\theme.css", kind="Edit"), said("Done.")))
        self.assertIn("references/visual-judgment.md", text)
        self.assertNotIn("scenario-testing.md", text)
        for path in ("C:\\app\\src\\api.ts", "C:\\app\\src\\Panel.test.tsx"):
            with self.subTest(path=path):
                self.assertEqual({}, self.stop(prompt(), load("assay:ui-delivery"), write(path, kind="Edit"),
                                               said("Done.")))

    def test_russian_documentation_calls_for_languages(self):
        text = self.feedback(self.stop(prompt(), load("assay:technical-writing"),
                                       write("C:\\repo\\docs\\guide.md", RUSSIAN), said("Готово.")))
        self.assertIn("technical-writing: references/languages.md", text)
        # Control: English prose, Russian in code, a single Russian word and an agent memory note.
        for path, content in (("C:\\repo\\docs\\guide.md", "This section explains the branch check. " * 3),
                              ("C:\\repo\\tool.py", RUSSIAN), ("C:\\repo\\docs\\guide.md", "See «пример»."),
                              ("C:\\agent\\.claude\\projects\\p\\memory\\lesson.md", RUSSIAN)):
            with self.subTest(path=path, content=content[:20]):
                self.assertEqual({}, self.stop(prompt(), load("assay:technical-writing"), write(path, content),
                                               said("Done.")))

    def test_several_rows_share_one_note(self):
        text = self.feedback(self.stop(prompt(), load("assay:code-change", "s1"), load("assay:ui-delivery", "s2"),
                                       write("C:\\app\\src\\App.vue", kind="Edit"), said(CLAIM_EN)))
        self.assertEqual(2, text.count("\n- "))
        self.assertIn("vue-structure.md", text)
        self.assertIn("visual-judgment.md", text)
        self.assertNotIn("search-and-coverage", text)  # evidence-research was not loaded.

    def test_a_sign_from_an_earlier_turn_does_not_count(self):
        self.assertEqual({}, self.stop(prompt("first"), load("assay:code-change"),
                                       write("C:\\app\\src\\App.vue"), said("ok"), prompt(), said("Done.")))

    def test_disabled_rules_and_skills_drop_their_rows(self):
        entries = (prompt(), load("assay:code-change"), write("C:\\app\\src\\App.vue"), said("Done."))
        event = {**self.base, "hook_event_name": "Stop", "transcript_path": self.transcript(*entries),
                 "last_assistant_message": ""}
        self.feedback(branches.stopped(event))
        rest = [rule for rule in branches.RULES if rule != "branch-vue-structure"]
        self.assertEqual({}, branches.stopped(event, rest))
        self.assertEqual({}, branches.stopped(event, branches.RULES, {"ui-delivery", "evidence-research"}))


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
        self.assertIn("Assay branch check", result["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(({}, None), process(stop, "claude", self.configured(disabled_rules=["coverage-claims"])))
        self.assertEqual(({}, None), process(stop, "codex", self.environment))

    def test_a_row_rule_or_its_skill_turns_that_row_off(self):
        stop = self.stop_event(prompt(), load("assay:code-change"), write("C:\\app\\src\\App.vue"), said("Done."))
        text = process(stop, "claude", self.environment)[0]["hookSpecificOutput"]["additionalContext"]
        self.assertIn("vue-structure.md", text)
        # The report check joins the branch note in one continuation, and has its own rule.
        self.assertIn("Assay report check", text)
        rest = process(stop, "claude", self.configured(disabled_rules=["branch-vue-structure"]))[0]
        self.assertNotIn("Assay branch check", rest["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(({}, None), process(stop, "claude", self.configured(
            disabled_rules=["branch-vue-structure", "report-verification"])))
        self.assertEqual(({}, None), process(stop, "claude", self.configured(disabled_skills=["skill/code-change"])))

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
        self.assertIn("Assay branch check", text)


if __name__ == "__main__":
    unittest.main()
