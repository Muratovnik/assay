"""Claude rerun note: the fifth run of one scenario since the owner's last message names the diagnostic reference once."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import activation, reruns
from runtime.cli import process

RUN = "pwsh -NoProfile -File tmp/e2e/run.ps1 > tmp/e2e/run{n}.log 2>&1; echo exit $?; tail -15 tmp/e2e/run{n}.log"
ABSOLUTE = "pwsh -NoProfile -File C:/work/tmp/worktrees/scenario/tmp/e2e/run.ps1"
REFERENCE = "C:\\cache\\assay\\skills\\code-change\\references\\diagnostic-reproducer.md"
LAST = reruns.THRESHOLD


def call(command, ident, tool="Bash"):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": ident, "name": tool, "input": {"command": command}}]}}


def result(ident, text="exit 0"):
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": ident, "content": text}]}}


def run(n, ident=None, command=None):
    ident = ident or f"r{n}"
    return [call(command or RUN.format(n=n), ident), result(ident)]


def runs(first, last, command=None, prefix="r"):
    """Completed runs numbered first to last."""
    return [entry for n in range(first, last + 1) for entry in run(n, f"{prefix}{n}", command)]


def current(n, command=None, ident=None):
    # Claude Code writes the call into the transcript before PreToolUse runs.
    return call(command or RUN.format(n=n), ident or f"r{n}")


def owner(text="Do the task", prompt_id="p1"):
    return {"type": "user", "turnOrigin": "human", "promptSource": "sdk", "promptId": prompt_id,
            "message": {"role": "user", "content": text}}


def notification(prompt_id):
    return {"type": "user", "turnOrigin": "task_notification", "promptSource": "system", "promptId": prompt_id,
            "message": {"role": "user", "content": "<task-notification> <task-id>b1</task-id> completed"}}


def summary():
    return [{"type": "system", "subtype": "compact_boundary"},
            {"type": "user", "isCompactSummary": True, "isVisibleInTranscriptOnly": True, "turnOrigin": "task_notification",
             "message": {"role": "user", "content": "This session is being continued from a previous conversation"}}]


def read(path=REFERENCE, ident="read1"):
    return [{"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": ident, "name": "Read", "input": {"file_path": path}}]}}, result(ident, "text")]


class SignatureTests(unittest.TestCase):
    def test_one_scenario_has_one_signature_whatever_its_path_and_redirections(self):
        for command in (ABSOLUTE, RUN.format(n=3), "cd C:/work && pwsh -NoProfile -File tmp/e2e/run.ps1 *> out.log",
                        "& ./tmp/e2e/run.ps1", "powershell.exe -File .\\tmp\\e2e\\run.ps1"):
            with self.subTest(command=command):
                self.assertEqual("e2e/run.ps1", reruns.signature(command))

    def test_arguments_are_part_of_the_scenario(self):
        cases = {
            ".venv/Scripts/python.exe -B -m unittest tools.test_app 2>&1 | tail -3": "unittest tools.test_app",
            "python -m pytest tests/test_app.py -k parse": "pytest tests/test_app.py -k parse",
            "uv run pytest -q": "pytest -q",
            "uv run --with pypdf python tools/probe.py": "tools/probe.py",
            "dotnet test tests/App.Tests.csproj --filter Ship > log.txt": "dotnet test tests/app.tests.csproj --filter ship",
            "npm run test:unit": "npm run test:unit",
            "npx vitest run src/panel": "npx vitest run src/panel",
            "go test ./...": "go test ./...",
            "python -B tools/check.py --all": "tools/check.py --all",
            "& ./tmp/e2e/run.ps1 -Fast": "e2e/run.ps1 -fast",
            "python C:/work/tools/eol.py C:/work/src/app/main.cs --check": "tools/eol.py app/main.cs --check",
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self.assertEqual(expected, reruns.signature(command))
        for one, other in (("python -m pytest tests/a.py", "python -m pytest tests/b.py"),
                           ("python tools/eol.py b4fc1aa --check", "python tools/eol.py c8ccc48 --check"),
                           ("python tools/workbench.py status", "python tools/workbench.py check")):
            with self.subTest(one=one):
                self.assertNotEqual(reruns.signature(one), reruns.signature(other))

    def test_inline_code_edits_and_other_commands_are_not_runs(self):
        for command in ("python - <<'EOF'\nopen('tmp/e2e/run.ps1')\nEOF", "python -I -c \"import app.py\"",
                        "mkdir -p tmp && cat > tmp/run.ps1 <<'EOF'\npwsh -File x.ps1\nEOF",
                        "sed -i 's/a/b/' tmp/e2e/run.ps1", "git add src/app.py tests/test_app.py",
                        "git commit -m 'run tools/check.py'", "npm run build", "pwsh -Command \"./x.ps1\"",
                        "grep -n run tmp/e2e/run.ps1", "cat tmp/e2e/run3.log", "", None, 7):
            with self.subTest(command=command):
                self.assertIsNone(reruns.signature(command))

    def test_the_activation_list_matches_the_module(self):
        self.assertEqual(reruns.RULES, activation.RERUN_RULES)
        rules = activation.load_rules(ROOT)[0]
        self.assertEqual(frozenset(reruns.RULES), rules.rerun_rules)
        self.assertEqual(frozenset(), activation.load_rules(ROOT, disabled_rules=list(reruns.RULES))[0].rerun_rules)
        # The note names a reference, not a skill to load, so the skill check does not carry it.
        self.assertEqual(frozenset(reruns.RULES), activation.load_rules(ROOT, disabled_rules=["skill-check"])[0].rerun_rules)


class NoteTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.data = self.directory / "data"

    def transcript(self, *entries, name="session.jsonl"):
        path = self.directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        flat = [item for entry in entries for item in (entry if isinstance(entry, list) else [entry])]
        path.write_text("".join(json.dumps(entry) + "\n" for entry in flat), encoding="utf-8")
        return str(path)

    def pre(self, path, n=LAST, ident=None, command=None, **extra):
        ident = ident or f"r{n}"
        return {"session_id": "s1", "cwd": "work", "hook_event_name": "PreToolUse", "tool_name": "Bash",
                "tool_input": {"command": command or RUN.format(n=n)}, "tool_use_id": ident, "prompt_id": "p9",
                "transcript_path": path, **extra}

    def environment(self, **options):
        if not options:
            return {"CLAUDE_PLUGIN_DATA": str(self.data)}
        path = self.directory / "hooks.json"
        path.write_text(json.dumps({**options, "state_dir": str(self.data)}), encoding="utf-8")
        return {"ASSAY_HOOK_CONFIG": str(path)}

    def run_event(self, event, environment=None):
        output, error = process(event, "claude", self.environment() if environment is None else environment)
        self.assertIsNone(error)
        return output

    def note(self, output):
        self.assertEqual({"hookEventName", "additionalContext"}, set(output["hookSpecificOutput"]))
        return output["hookSpecificOutput"]["additionalContext"]

    def test_the_fifth_run_since_the_owner_names_the_reference_once(self):
        self.assertEqual(5, LAST)
        path = self.transcript(owner(), runs(1, 4), current(5))
        text = self.note(self.run_event(self.pre(path)))
        self.assertIn("run 5 of the same scenario (e2e/run.ps1)", text)
        self.assertIn("assay:code-change reference references/diagnostic-reproducer.md", text)
        self.assertNotIn("tmp/e2e/run5.log", text)
        self.assertLessEqual(len(text), 360)
        path = self.transcript(owner(), runs(1, 5), current(6))
        self.assertEqual({}, self.run_event(self.pre(path, 6)))

    def test_four_runs_are_not_a_loop(self):
        path = self.transcript(owner(), runs(1, 3), current(4))
        self.assertEqual({}, self.run_event(self.pre(path, 4)))

    def test_task_notifications_and_a_compaction_do_not_restart_the_count(self):
        path = self.transcript(owner(), run(1, command=ABSOLUTE), notification("p2"), runs(2, 3), *summary(), run(4),
                               notification("p3"), current(5))
        self.assertIn("run 5", self.note(self.run_event(self.pre(path))))

    def test_an_owner_message_restarts_the_count_and_gets_its_own_note(self):
        path = self.transcript(owner(), runs(1, 2), owner("Think first", "p2"), runs(3, 5), current(6))
        self.assertEqual({}, self.run_event(self.pre(path, 6)))
        path = self.transcript(owner(), runs(1, 5), owner("Think first", "p2"), runs(6, 9), current(10))
        self.assertIn("run 5", self.note(self.run_event(self.pre(path, 10))))

    def test_a_different_scenario_is_counted_and_named_separately(self):
        other = "python -m pytest tests/test_app.py"
        path = self.transcript(owner(), runs(1, 4, other, "o"), runs(1, 2), current(5, other, "o5"))
        self.assertIn("(pytest tests/test_app.py)", self.note(self.run_event(self.pre(path, command=other, ident="o5"))))
        path = self.transcript(owner(), runs(1, 4, other, "o"), runs(1, 4), current(5))
        self.assertIn("(e2e/run.ps1)", self.note(self.run_event(self.pre(path))))

    def test_a_read_reference_keeps_it_silent_until_a_compaction_drops_it(self):
        for label, entries in {"a Read": read(), "a shell read": [call(
                "Get-Content C:/cache/assay/skills/code-change/references/diagnostic-reproducer.md", "g1"),
                result("g1", "text")]}.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as scratch:
                self.data = Path(scratch)
                path = self.transcript(entries, owner(), runs(1, 4), current(5))
                self.assertEqual({}, self.run_event(self.pre(path)))
        path = self.transcript(owner(), read(), runs(1, 2), *summary(), runs(3, 4), current(5))
        self.assertIn("run 5", self.note(self.run_event(self.pre(path))))
        # Another skill's reference of the same name does not count.
        path = self.transcript(owner(prompt_id="p2"), read("C:\\x\\skills\\other\\references\\diagnostic-reproducer.md"),
                               runs(1, 4), current(5), name="other.jsonl")
        self.assertIn("run 5", self.note(self.run_event(self.pre(path))))

    def test_a_subagent_is_judged_by_its_own_transcript(self):
        base = self.transcript(owner(), name="s1.jsonl")
        worker = {"type": "user", "isSidechain": True, "message": {"role": "user", "content": "Packet: fix the scenario"}}
        entries = [worker, *[{**entry, "isSidechain": True} for entry in [*runs(1, 4), current(5)]]]
        self.transcript(entries, name="s1/subagents/agent-a1.jsonl")
        self.assertIn("run 5", self.note(self.run_event(self.pre(base, agent_id="a1"))))
        # The root agent's own count does not include the worker's runs.
        self.assertEqual({}, self.run_event(self.pre(self.transcript(owner(), current(5), name="s1.jsonl"))))

    def test_disabled_rule_or_skill_no_data_and_other_events_stay_silent(self):
        path = self.transcript(owner(), runs(1, 4), current(5))
        for options in ({"disabled_rules": ["rerun-diagnostic-reproducer"]}, {"disabled_skills": ["skill/code-change"]}):
            with self.subTest(options=options):
                self.assertEqual({}, self.run_event(self.pre(path), self.environment(**options)))
        self.assertEqual({}, self.run_event(self.pre(path), {}))
        for name in ("PostToolUse", "Stop"):
            self.assertNotIn("rerun note", json.dumps(self.run_event({**self.pre(path), "hook_event_name": name})))
        self.assertEqual({}, self.run_event(self.pre(path, session_id="")))
        self.assertEqual({}, self.run_event(self.pre(str(self.directory / "missing.jsonl"))))
        output, _ = process(self.pre(path), "codex", self.environment())
        self.assertNotIn("rerun note", json.dumps(output))

    def test_a_skill_note_on_the_same_call_goes_first(self):
        command = "python -B tools/check.py --all"
        fetch = "curl -sL https://docs.example.dev/x -o x.html; " + command
        path = self.transcript(owner(), runs(1, 4, command, "c"), current(5, fetch, "c5"))
        output = self.run_event(self.pre(path, command=fetch, ident="c5"))["hookSpecificOutput"]
        # The research row refuses its first call, and the refusal speaks alone.
        self.assertEqual("deny", output["permissionDecision"])
        self.assertIn("assay:evidence-research", output["permissionDecisionReason"])
        self.assertNotIn("rerun note", json.dumps(output))


if __name__ == "__main__":
    unittest.main()
