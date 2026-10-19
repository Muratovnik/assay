"""Claude mid-turn skill note: a tool call that shows a skill the session has not loaded names it once; no model runs."""
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
from runtime import activation, cli, midturn
from runtime.cli import process

APP = "C:\\work\\src\\app.py"
TESTS = "C:\\work\\tests\\test_app.py"
PAGE = "C:\\work\\web\\src\\Panel.vue"
GUIDE = "C:\\work\\docs\\guide.md"
SKILL = "C:\\work\\skills\\parser\\SKILL.md"
DOCS = "https://docs.example.dev/guide/hooks"
FETCH = f"curl -sL {DOCS} -o guide.html"


def tool(name, data, ident):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": ident, "name": name, "input": data}]}}


def returned(ident, text="ok"):
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": ident, "content": text}]}}


def prompt(text="Do the task"):
    return {"type": "user", "message": {"role": "user", "content": text}}


def load(skill="assay:test-writing", ident="s1"):
    return [tool("Skill", {"skill": skill}, ident), returned(ident, "Launching skill")]


class SignTableTests(unittest.TestCase):
    def rules(self, call, data):
        return [rule for rule, _ in midturn.signs(call, data)]

    def edit(self, path):
        return self.rules("Edit", {"file_path": path, "old_string": "a", "new_string": "b"})

    def test_each_sign_calls_for_its_skill(self):
        cases = {
            "midturn-code-change": [APP, "C:\\work\\cmd\\main.go", "/srv/work/lib/Rules.cs", "C:\\work\\tools\\build.ps1",
                                    "C:\\work\\tmp\\worktrees\\task\\src\\core.py"],
            "midturn-test-writing": [TESTS, "C:\\work\\src\\app_test.go", "C:\\work\\web\\src\\panel.spec.ts",
                                     "C:\\work\\tests\\Contracts.cs", "C:\\work\\conftest.py",
                                     "C:\\work\\src\\test_parser.py"],
            "midturn-ui-delivery": [PAGE, "C:\\work\\app\\styles\\global.css", "C:\\work\\web\\Panel.tsx",
                                    "C:\\work\\web\\index.html"],
            "midturn-technical-writing": ["C:\\work\\README.md", "C:\\work\\docs\\how-to\\setup.md", "C:\\work\\docs\\adr\\0001-x.md",
                                          "C:\\work\\docs\\ru\\README.ru.md"],
            "midturn-skill-evaluation": [SKILL, "C:\\work\\skills\\parser\\references\\rules.md",
                                         "C:\\work\\hooks\\activation-rules.toml"],
        }
        for rule, paths in cases.items():
            for path in paths:
                with self.subTest(path=path):
                    self.assertEqual([rule], self.edit(path))
        for call, data in (("Write", {"file_path": APP, "content": "x"}), ("MultiEdit", {"file_path": APP, "edits": []}),
                           ("NotebookEdit", {"notebook_path": APP})):
            with self.subTest(call=call):
                self.assertEqual(["midturn-code-change"], self.rules(call, data))

    def test_a_web_tool_or_an_external_fetch_calls_for_evidence_research(self):
        research = ["midturn-evidence-research"]
        self.assertEqual(research, self.rules("WebFetch", {"url": DOCS, "prompt": "q"}))
        self.assertEqual(research, self.rules("WebSearch", {"query": "tomllib write"}))
        for command in (FETCH, f"wget {DOCS}", f"cd x && curl.exe -L {DOCS}", f"$p = Invoke-WebRequest -Uri '{DOCS}'",
                        f"cd /tmp/x; irm {DOCS}", f"LC_ALL=C curl -s {DOCS} | head"):
            for shell in ("Bash", "PowerShell"):
                with self.subTest(command=command):
                    self.assertEqual(research, self.rules(shell, {"command": command}))

    def test_near_valid_files_call_for_nothing(self):
        for path in ("C:\\work\\docs\\plans\\2026-roadmap.md", "C:\\work\\docs\\research\\notes\\study.md",
                     "C:\\work\\plans\\next.md", "C:\\work\\CLAUDE.md", "C:\\work\\AGENTS.md", "C:\\work\\CHANGELOG.md",
                     "C:\\work\\docs\\CHANGELOG.md", "C:\\work\\docs\\AGENTS.md",
                     "C:\\work\\docs\\MEMORY.md",
                     "C:\\work\\notes\\todo.md", "C:\\agent\\.claude\\projects\\x\\memory\\note.md",
                     "C:\\work\\package-lock.json", "C:\\work\\config.yaml", "C:\\work\\data.json",
                     "C:\\work\\node_modules\\lib\\index.js", "C:\\work\\dist\\app.min.js", "C:\\work\\src\\types.d.ts",
                     "C:\\work\\src\\api_pb2.py", "C:\\work\\web\\tests\\Panel.test.css", "C:\\work\\tmp\\probe.py",
                     "C:\\agent\\AppData\\Local\\Temp\\claude\\scratchpad\\dump.py", "C:\\work\\tmp\\worktrees\\task\\tmp\\edit.py",
                     "C:\\work\\.private\\evidence\\parse.py", "", None):
            with self.subTest(path=path):
                self.assertEqual([], self.edit(path))

    def test_near_valid_commands_call_for_nothing(self):
        for command in ("curl -s http://localhost:8642/health", "curl http://127.0.0.1:8769/api -H 'X: 1'",
                        "Invoke-RestMethod -Uri http://[::1]:9000/x", "ls -la", "git commit -m 'mention curl https://x.dev/a'",
                        f"git clone {DOCS}", f"curl -sS -o /dev/null -w '%{{http_code}}' {DOCS}", f"curl -I {DOCS}",
                        f"curl --head {DOCS}", f"Invoke-WebRequest {DOCS} -Method Head", "gh api repos/o/r/releases", "gh api https://api.github.com/repos/o/r",
                        "curl --version", f"echo {DOCS}", "pip install requests", "curl https://example.org/x",
                        f"curl -s http://localhost:1/x ; echo {DOCS}"):
            with self.subTest(command=command):
                self.assertEqual([], self.rules("Bash", {"command": command}))
        self.assertEqual([], self.rules("Bash", {"command": 7}))
        self.assertEqual([], self.rules("Edit", "not an object"))
        self.assertEqual([], self.rules("Read", {"file_path": APP}))

    def test_the_first_target_decides_and_a_later_external_fetch_still_counts(self):
        self.assertEqual([], self.rules("Bash", {"command": f"curl -s http://localhost:1/x -d '{DOCS}'"}))
        self.assertEqual(["midturn-evidence-research"], self.rules(
            "Bash", {"command": f"curl -s http://localhost:1/x; curl -sL {DOCS}"}))

    def test_evidence_names_a_file_or_a_host_never_a_url(self):
        self.assertEqual([("midturn-code-change", "app.py")], midturn.signs("Edit", {"file_path": APP}))
        self.assertEqual([("midturn-evidence-research", "docs.example.dev")],
                         midturn.signs("Bash", {"command": f"curl -sL {DOCS}?token=secret"}))
        self.assertEqual([("midturn-evidence-research", "docs.example.dev")], midturn.signs("WebFetch", {"url": DOCS}))
        self.assertEqual([("midturn-evidence-research", "web search")], midturn.signs("WebSearch", {"query": "q"}))

    def test_an_owner_question_calls_for_critical_discussion_and_names_its_header(self):
        options = [{"label": "A", "description": "a"}, {"label": "B", "description": "b"}]
        asked = {"questions": [{"question": "Which approach?", "header": "Approach", "options": options,
                                "multiSelect": False}]}
        self.assertEqual([("midturn-critical-discussion", "Approach")], midturn.signs("AskUserQuestion", asked))
        for data in ({"questions": []}, {"questions": ["text"]}, {"questions": [{"header": "  "}]}, {}):
            with self.subTest(data=data):
                self.assertEqual([("midturn-critical-discussion", "question")], midturn.signs("AskUserQuestion", data))
        self.assertEqual([], midturn.signs("AskUserQuestion", "not an object"))
        self.assertEqual([], midturn.signs("ExitPlanMode", {"plan": "x"}))

    def test_the_activation_list_matches_the_table(self):
        self.assertEqual(midturn.RULES, activation.MIDTURN_RULES)
        self.assertEqual(len(midturn.RULES), len(set(midturn.RULES)))
        shipped = {row.skill for row in midturn.ROWS}
        catalog = {rule["skill"].split("/", 1)[1] for rule in activation.load_rules(ROOT)[0]}
        self.assertLessEqual(shipped, catalog)

    def test_every_note_is_short_and_states_facts(self):
        for row in midturn.ROWS:
            message = midturn.text(row, "x" * 200)
            with self.subTest(rule=row.rule):
                # About 300 characters with a usual file name; the evidence is cut at 80.
                self.assertLessEqual(len(midturn.text(row, "test_app.py")), 320)
                self.assertLessEqual(len(message), 400)
                self.assertIn(f"assay:{row.skill}", message)
                self.assertIn(row.decision, message)
                self.assertNotIn("must", message.lower())


class NoteTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.data = self.directory / "data"
        self.now = 1000.0
        self.names = {row.skill for row in midturn.ROWS}

    def environment(self, **options):
        if not options:
            return {"CLAUDE_PLUGIN_DATA": str(self.data)}
        path = self.directory / "hooks.json"
        path.write_text(json.dumps({**options, "state_dir": str(self.data)}), encoding="utf-8")
        return {"ASSAY_HOOK_CONFIG": str(path)}

    def transcript(self, *entries, name="session.jsonl"):
        path = self.directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        flat = [item for entry in entries for item in (entry if isinstance(entry, list) else [entry])]
        path.write_text("".join(json.dumps(entry) + "\n" for entry in flat), encoding="utf-8")
        return str(path)

    def pre(self, call="Edit", data=None, **extra):
        data = {"file_path": TESTS, "old_string": "a", "new_string": "b"} if data is None else data
        return {"session_id": "s1", "cwd": "work", "hook_event_name": "PreToolUse", "tool_name": call,
                "tool_input": data, "prompt_id": "p1", **extra}

    def run_event(self, event, environment=None, client="claude"):
        result, error = process(event, client, self.environment() if environment is None else environment)
        self.assertIsNone(error)
        return result

    def note(self, result):
        output = result["hookSpecificOutput"]
        self.assertEqual({"hookEventName", "additionalContext"}, set(output))
        self.assertEqual("PreToolUse", output["hookEventName"])
        return output["additionalContext"]

    def test_a_sign_without_the_skill_names_it_once(self):
        text = self.note(self.run_event(self.pre()))
        self.assertIn("assay:test-writing", text)
        self.assertIn("edits a test file (test_app.py)", text)
        self.assertNotIn("C:\\work", text)
        self.assertEqual({}, self.run_event(self.pre()))

    def test_a_loaded_skill_keeps_it_silent_whether_the_load_was_a_skill_call_or_a_read(self):
        self.run_event(self.pre("Skill", {"skill": "assay:test-writing"}))
        self.assertEqual({}, self.run_event(self.pre()))
        self.run_event(self.pre("Read", {"file_path": "C:\\cache\\assay\\skills\\code-change\\SKILL.md"}, prompt_id="p2"))
        self.assertEqual({}, self.run_event(self.pre("Edit", {"file_path": APP}, prompt_id="p2")))

    def test_a_load_only_the_transcript_shows_keeps_it_silent_and_is_remembered(self):
        for label, entries in {
            "a skill call before this session id": [prompt(), load("assay:test-writing"), prompt("next")],
            "a skill that compaction kept": [{"type": "system", "subtype": "compact_boundary"}, {
                "type": "attachment", "attachment": {"type": "invoked_skills", "skills": [{"name": "test-writing"}]}},
                prompt("continue")],
        }.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as scratch:
                self.data = Path(scratch)
                path = self.transcript(*entries, name="resumed.jsonl")
                self.assertEqual({}, self.run_event(self.pre(transcript_path=path, session_id="resumed")))
                # The records now hold the load, so an unreadable transcript no longer matters.
                self.assertEqual({}, self.run_event(self.pre(transcript_path=str(self.directory / "gone.jsonl"),
                                                             session_id="resumed", prompt_id="p9")))

    def test_a_load_before_a_compaction_that_did_not_keep_it_is_not_counted(self):
        path = self.transcript(prompt(), load("assay:test-writing"), {"type": "system", "subtype": "compact_boundary"},
                               prompt("continue"))
        self.assertIn("assay:test-writing", self.note(self.run_event(self.pre(transcript_path=path))))

    def test_an_unreadable_transcript_leaves_the_records_as_the_only_evidence(self):
        for path in (None, "", str(self.directory / "gone.jsonl"), 7):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as scratch:
                self.data = Path(scratch)
                self.assertIn("assay:test-writing", self.note(self.run_event(self.pre(transcript_path=path))))

    def test_one_note_per_skill_request_and_agent(self):
        self.assertIn("test-writing", self.note(self.run_event(self.pre())))
        self.assertEqual({}, self.run_event(self.pre("Write", {"file_path": "C:\\work\\tests\\test_other.py", "content": "x"})))
        # Another skill in the same request, another request, another agent each get their own.
        self.assertIn("assay:code-change", self.note(self.run_event(self.pre("Edit", {"file_path": APP}))))
        self.assertIn("test-writing", self.note(self.run_event(self.pre(prompt_id="p2"))))
        self.assertIn("test-writing", self.note(self.run_event(self.pre(agent_id="worker"))))
        self.assertEqual({}, self.run_event(self.pre(agent_id="worker")))
        self.assertIn("test-writing", self.note(self.run_event(self.pre(session_id="other"))))

    def test_two_parallel_calls_of_one_request_are_named_once(self):
        event, nested, real = self.pre(), [], midturn._shown_loaded

        def racing(*args, **kwargs):
            # The second call arrives while the first is still reading the transcript.
            if not nested:
                nested.append(None)
                nested[0] = self.run_event(event)
            return real(*args, **kwargs)

        with patch.object(midturn, "_shown_loaded", racing):
            outer = self.run_event(event)
        self.assertIn("assay:test-writing", self.note(nested[0]))
        self.assertEqual({}, outer)

    def test_without_a_prompt_id_the_note_comes_once_per_agent(self):
        event = self.pre()
        del event["prompt_id"]
        self.assertIn("test-writing", self.note(self.run_event(event)))
        self.assertEqual({}, self.run_event(event))

    def test_a_subagent_is_judged_by_its_own_loads(self):
        # The root loaded the skill; the worker did not.
        self.run_event(self.pre("Skill", {"skill": "assay:test-writing"}))
        self.assertIn("test-writing", self.note(self.run_event(self.pre(agent_id="a1"))))
        # A worker's own transcript shows its load even though its records do not.
        session = self.directory / "s2"
        own = session / "subagents" / "agent-a2.jsonl"
        self.transcript(prompt(), load("assay:test-writing"), name=str(own.relative_to(self.directory)))
        main = str(self.directory / "s2.jsonl")
        self.assertEqual({}, self.run_event(self.pre(agent_id="a2", session_id="s2", transcript_path=main)))
        # The path may also arrive ready-made.
        other = self.transcript(prompt(), load("assay:test-writing"), name="own.jsonl")
        self.assertEqual({}, self.run_event(self.pre(agent_id="a3", agent_transcript_path=other)))

    def test_a_root_agent_is_not_judged_by_a_workers_transcript(self):
        path = self.transcript(prompt(), name="s1.jsonl")
        self.transcript(prompt(), load("assay:test-writing"), name="s1/subagents/agent-a1.jsonl")
        self.assertIn("test-writing", self.note(self.run_event(self.pre(transcript_path=path))))

    def test_the_deny_form_refuses_the_first_call_and_passes_the_repeat(self):
        environment = self.environment(skill_note_form="deny")
        result = self.run_event(self.pre(), environment)
        output = result["hookSpecificOutput"]
        self.assertEqual("deny", output["permissionDecision"])
        reason = output["permissionDecisionReason"]
        self.assertTrue(reason.startswith("Assay: "))
        self.assertIn("assay:test-writing", reason)
        self.assertNotIn("additionalContext", output)
        self.assertEqual({}, self.run_event(self.pre(), environment))
        # Loading the skill before the first call needs no refusal at all.
        self.run_event(self.pre("Skill", {"skill": "assay:code-change"}), environment)
        self.assertEqual({}, self.run_event(self.pre("Edit", {"file_path": APP}), environment))

    def test_an_owner_question_without_the_skill_is_refused_once_under_either_form(self):
        asked = {"questions": [{"question": "Which approach?", "header": "Approach", "multiSelect": False,
                                "options": [{"label": "A", "description": "a"}, {"label": "B", "description": "b"}]}]}
        for options in ({}, {"skill_note_form": "deny"}):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as scratch:
                self.data = Path(scratch)
                environment = self.environment(**options)
                output = self.run_event(self.pre("AskUserQuestion", asked), environment)["hookSpecificOutput"]
                # A note would reach the model only after the owner answered, so the first call is refused.
                self.assertEqual("deny", output["permissionDecision"])
                self.assertIn("asks the owner to choose (Approach)", output["permissionDecisionReason"])
                self.assertIn("assay:critical-discussion", output["permissionDecisionReason"])
                self.assertNotIn("Which approach?", output["permissionDecisionReason"])
                self.assertEqual({}, self.run_event(self.pre("AskUserQuestion", asked), environment))
                # A later request with the skill loaded asks without a refusal.
                self.run_event(self.pre("Skill", {"skill": "assay:critical-discussion"}, prompt_id="p2"), environment)
                self.assertEqual({}, self.run_event(self.pre("AskUserQuestion", asked, prompt_id="p2"), environment))
                # The other rows keep the note form unless the option says deny.
                result = self.run_event(self.pre(prompt_id="p3"), environment)["hookSpecificOutput"]
                self.assertEqual("deny" if options else None, result.get("permissionDecision"))
        with tempfile.TemporaryDirectory() as scratch:
            self.data = Path(scratch)
            environment = self.environment(disabled_rules=["midturn-critical-discussion"])
            self.assertEqual({}, self.run_event(self.pre("AskUserQuestion", asked), environment))

    def test_the_default_form_is_the_note_and_both_forms_say_the_same(self):
        self.assertEqual("note", cli.options({})["skill_note_form"])
        self.assertEqual("deny", cli.options({"ASSAY_HOOK_CONFIG": self._config(skill_note_form="deny")})["skill_note_form"])
        note = self.note(self.run_event(self.pre()))
        with tempfile.TemporaryDirectory() as scratch:
            self.data = Path(scratch)
            reason = self.run_event(self.pre(), self.environment(skill_note_form="deny"))["hookSpecificOutput"][
                "permissionDecisionReason"]
        self.assertTrue(reason.startswith("Assay: " + note))

    def _config(self, **options):
        path = self.directory / "options.json"
        path.write_text(json.dumps(options), encoding="utf-8")
        return str(path)

    def test_an_invalid_form_or_an_unknown_option_is_rejected(self):
        for form in ("block", "", None, 1, ["note"]):
            with self.subTest(form=form), self.assertRaisesRegex(ValueError, "skill note form"):
                cli.options({"ASSAY_HOOK_CONFIG": self._config(skill_note_form=form)})
        with self.assertRaisesRegex(ValueError, "unknown hook option"):
            cli.options({"ASSAY_HOOK_CONFIG": self._config(skill_notes=True)})

    def test_a_routing_or_profile_answer_on_the_same_call_wins(self):
        event = self.pre("Edit", {"file_path": APP}, agent_type="evidence-reviewer", agent_id="r1")
        result = self.run_event(event)
        self.assertEqual("deny", result["hookSpecificOutput"]["permissionDecision"])
        self.assertNotIn("assay:code-change", json.dumps(result))
        # The refused call used up nothing: the same call from an ordinary agent is still named.
        self.assertIn("assay:code-change", self.note(self.run_event(self.pre("Edit", {"file_path": APP}, agent_id="w1"))))

    def test_rules_skills_and_the_skill_check_turn_the_note_off(self):
        for options in ({"disabled_rules": ["midturn-test-writing"]}, {"disabled_skills": ["skill/test-writing"]},
                        {"disabled_rules": ["skill-check"]}):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as scratch:
                self.data = Path(scratch)
                self.assertEqual({}, self.run_event(self.pre(), self.environment(**options)))
        # A disabled row leaves the others alone.
        environment = self.environment(disabled_rules=["midturn-test-writing"])
        self.assertIn("assay:code-change", self.note(self.run_event(self.pre("Edit", {"file_path": APP}), environment)))
        with self.assertRaisesRegex(ValueError, "unknown disabled rule"):
            activation.load_rules(ROOT, disabled_rules=["midturn-tests"])
        for rule in midturn.RULES:
            activation.load_rules(ROOT, disabled_rules=[rule])

    def test_no_data_directory_codex_and_other_events_stay_silent(self):
        self.assertEqual({}, self.run_event(self.pre(), {}))
        self.assertEqual({}, self.run_event(self.pre(), client="codex"))
        for name in ("PostToolUse", "Stop", "UserPromptSubmit"):
            self.assertNotIn("Assay skill note", json.dumps(self.run_event({**self.pre(), "hook_event_name": name})))
        self.assertEqual({}, self.run_event(self.pre(session_id="")))
        self.assertEqual({}, self.run_event(self.pre(agent_id="")))

    def test_the_launch_reminder_is_left_alone_and_a_launch_shows_no_sign(self):
        result = self.run_event(self.pre("Agent", {"description": "review", "subagent_type": "worker", "prompt": "x"}))
        self.assertIn("Assay routing checkpoint", self.note(result))
        self.assertNotIn("Assay skill note", json.dumps(result))

    def test_the_records_are_bounded_and_hold_hashes_only(self):
        for index in range(midturn.MAX_RECORDS + 20):
            self.run_event(self.pre(prompt_id=f"p{index}"))
        from route_evidence.pipeline_store import PipelineStore
        with PipelineStore(self.data / "skill-note").transaction() as tx:
            records = tx.values("note")
        self.assertLessEqual(len(records), midturn.MAX_RECORDS)
        self.assertNotIn("p5", json.dumps(records))
        self.assertNotIn("test_app", json.dumps(records))

    def test_a_replayed_documentation_fetch_names_the_research_skill_only_without_it(self):
        chain = [self.pre("Bash", {"command": f"mkdir -p out && {FETCH}"}),
                 self.pre("Bash", {"command": f"curl -sL {DOCS}/more -o more.html"}),
                 self.pre("Read", {"file_path": "C:\\work\\out\\guide.html"})]
        first = [self.run_event(event) for event in chain]
        self.assertIn("assay:evidence-research", self.note(first[0]))
        self.assertIn("fetches an external source (docs.example.dev)", first[0]["hookSpecificOutput"]["additionalContext"])
        self.assertEqual([{}, {}], first[1:])
        with tempfile.TemporaryDirectory() as scratch:
            self.data = Path(scratch)
            self.run_event(self.pre("Skill", {"skill": "assay:evidence-research"}))
            self.assertEqual([{}, {}, {}], [self.run_event(event) for event in chain])

    def test_the_fetch_note_after_a_web_fetch_is_unchanged(self):
        result = self.run_event({**self.pre("WebFetch", {"url": DOCS, "prompt": "q"}), "hook_event_name": "PostToolUse"})
        self.assertIn("Assay source check", self.note({"hookSpecificOutput": {**result["hookSpecificOutput"],
                                                                              "hookEventName": "PreToolUse"}}))

    def test_doctor_reports_the_form(self):
        report = cli.doctor("claude", {"CLAUDE_PLUGIN_DATA": str(self.data)})
        self.assertEqual("note", report["skill_note_form"])


if __name__ == "__main__":
    unittest.main()
