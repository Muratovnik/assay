"""The Claude hook's early exit: which tool calls it answers before loading the checks, and that it answers them alike.

The oracle is the full path itself. Whenever the gate answers a call, `cli.process` on the same
event, with configured and seeded stores, must return {} and leave every stored record as it was.
The gate may send more calls the full path than needed; it must never answer one the full path
would answer or record.
"""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import activation, cli, gate, midturn, predicates, reruns, skill_gate, state
from route_evidence import route_table
from route_evidence.core import digest
from route_evidence.pipeline_store import PipelineStore

ENTRY = ROOT / "hooks/runtime/cli.py"
NOW = 1_000_000.0
# Modules the full path loads and the early exit must not: the rules, the stores and everything behind them.
CHECKS = ("route_evidence.core", "route_evidence.pipeline_store", "runtime.activation", "runtime.branches",
          "runtime.state", "sqlite3", "tomllib")
# No event run builds the command parser; its help formatter alone loads shutil and locale.
HEAVY = (*CHECKS, "argparse")
CLEAN = {k: v for k, v in os.environ.items()
         if not k.startswith(("ASSAY_", "CLAUDE_PLUGIN", "PLUGIN_DATA", "CLAUDE_CODE_EFFORT"))}


def event(tool, data=None, **fields):
    return {"hook_event_name": "PreToolUse", "session_id": "session-1", "cwd": "/work", "tool_name": tool,
            "tool_input": {} if data is None else data, **fields}


def raw(value):
    return json.dumps(value).encode()


# Calls no check reads, by tool class: (tool, input).
QUIET = [
    ("Grep", {"pattern": "TODO"}), ("Glob", {"pattern": "**/*.py"}), ("ToolSearch", {"query": "select:Monitor"}),
    ("mcp__planning__claim_work_item", {"id": "X-1"}), ("Monitor", {}), ("TaskStop", {}), ("SendMessage", {}),
    ("Read", {"file_path": "/work/src/app.py"}), ("Read", {"file_path": "/work/skills/parser/references/x.md"}),
    ("Read", {"file_path": "/work/skills/parser/SKILL.md.bak"}), ("Read", "not an object"),
    ("Edit", {"file_path": "/work/notes.txt"}), ("Edit", {"file_path": "/work/tmp/probe.py"}),
    ("Write", {"file_path": "/work/node_modules/pkg/index.js"}), ("Write", {"file_path": "/work/CLAUDE.md"}),
    ("MultiEdit", {"file_path": "/work/docs/plans/next.md"}), ("NotebookEdit", {"notebook_path": "/work/a.ipynb"}),
    ("Edit", {"file_path": None}), ("Edit", {}),
    ("Bash", {"command": "git status"}), ("Bash", {"command": "curl -sS http://localhost:8080/health"}),
    ("Bash", {"command": "curl -I https://docs.example.dev/guide"}), ("Bash", {"command": "git commit -m 'curl https://x.io'"}),
    ("Bash", {"command": "python -c 'print(1)'"}), ("PowerShell", {"command": "Get-ChildItem -Recurse"}),
    ("Bash", {}), ("Bash", {"command": 5}),
]
# Calls a check reads: (tool, input).
FULL = [
    ("Agent", {"description": "x"}), ("Task", {}), ("SubagentHandback", {"message": "done"}),
    ("Skill", {"skill": "assay:code-change"}), ("WebFetch", {"url": "https://docs.example.dev"}),
    ("WebSearch", {"query": "hooks"}), ("AskUserQuestion", {"questions": []}),
    ("Read", {"file_path": "/work/skills/code-change/SKILL.md"}),
    ("Read", {"file_path": "C:\\cache\\skills\\test-writing\\SKILL.md"}),
    ("Read", {"file_path": "/work/skills/unknown-skill/SKILL.md"}),
    ("Edit", {"file_path": "/work/src/app.py"}), ("Write", {"file_path": "/work/tests/test_app.py"}),
    ("MultiEdit", {"file_path": "/work/README.md"}), ("Edit", {"file_path": "/work/web/Panel.vue"}),
    ("NotebookEdit", {"notebook_path": "/work/src/model.py"}), ("Write", {"file_path": "/work/skills/x/SKILL.md"}),
    ("Bash", {"command": "curl -sL https://docs.example.dev/guide/hooks -o guide.html"}),
    ("Bash", {"command": "pytest -q tools"}), ("Bash", {"command": "uv run python tools/check.py"}),
    ("PowerShell", {"command": "pwsh -NoProfile -File tmp/e2e/run.ps1"}),
    ("PowerShell", {"command": "Invoke-WebRequest https://pypi.org/simple/x"}),
]


class PredicateTests(unittest.TestCase):
    def test_the_checks_use_the_predicates_the_gate_reads(self):
        # One definition each, so the gate and the checks cannot drift apart.
        self.assertIs(predicates.classify, midturn.classify)
        self.assertIs(predicates.external, midturn.external)
        self.assertIs(predicates.signature, reruns.signature)
        self.assertIs(predicates.LOADED_SKILL, skill_gate.SKILL_FILE)
        self.assertIs(predicates.SKILL_FILE, midturn.SKILL_FILE)
        self.assertIsNot(midturn.SKILL_FILE, skill_gate.SKILL_FILE)
        self.assertIs(predicates.reading_profile, cli.reading_profile)

    def test_the_gate_sends_every_tool_a_check_owns_the_full_path(self):
        owned = (route_table.SPAWN["claude"]["tools"] | {skill_gate.HANDBACK, midturn.QUESTION, "Skill"}
                 | midturn.WEB)
        self.assertLessEqual(owned, gate.FULL)

    def test_predicates_and_gate_import_without_the_checks(self):
        program = ("import json, sys\n"
                   f"sys.path.insert(0, {str(ROOT / 'hooks')!r})\n"
                   "import runtime.gate\n"
                   "print(json.dumps(sorted(m for m in sys.modules if m.startswith(('runtime', 'route_evidence')) "
                   f"or m in {list(HEAVY)!r} or m in ('dataclasses', 'hashlib', 'pathlib'))))\n")
        result = subprocess.run([sys.executable, "-I", "-B", "-c", program], capture_output=True, timeout=60, env=CLEAN)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["runtime", "runtime.gate", "runtime.predicates", "runtime.scratch"], json.loads(result.stdout))


class GateRuleTests(unittest.TestCase):
    def test_calls_no_check_reads_are_answered(self):
        for tool, data in QUIET:
            with self.subTest(tool=tool, data=data):
                self.assertIs(True, gate.quiet(raw(event(tool, data))))

    def test_calls_a_check_reads_take_the_full_path(self):
        for tool, data in FULL:
            with self.subTest(tool=tool, data=data):
                self.assertIs(False, gate.quiet(raw(event(tool, data))))

    def test_a_reading_role_takes_the_full_path_with_or_without_a_plugin_prefix(self):
        for role in ("evidence-reviewer", "assay:evidence-reviewer", "official-docs-researcher",
                     "other:assay:official-docs-researcher"):
            with self.subTest(role=role):
                self.assertIs(False, gate.quiet(raw(event("Grep", agent_type=role, agent_id="a1"))))
                self.assertIs(False, gate.quiet(raw(event("Grep", agent_type=role))))
        for role in ("general-purpose", "assay:worker", "evidence-reviewer-x", ""):
            with self.subTest(role=role):
                self.assertIs(True, gate.quiet(raw(event("Grep", agent_type=role, agent_id="a1"))))

    def test_a_subagent_without_its_type_takes_the_full_path(self):
        # Its role is known only from the record its start left.
        self.assertIs(False, gate.quiet(raw(event("Grep", agent_id="a1"))))
        self.assertIs(False, gate.quiet(raw(event("Grep", agent_id=""))))
        self.assertIs(False, gate.quiet(raw(event("Grep", agent_type=["evidence-reviewer"], agent_id="a1"))))

    def test_other_events_take_the_full_path(self):
        for name in ("UserPromptSubmit", "PostToolUse", "PostToolUseFailure", "SubagentStart", "SubagentStop",
                     "SessionStart", "SessionEnd", "Stop", "PostCompact", None):
            with self.subTest(name=name):
                self.assertIs(False, gate.quiet(raw({**event("Grep"), "hook_event_name": name})))

    def test_malformed_or_oversized_input_takes_the_full_path(self):
        ok = raw(event("Grep"))
        self.assertIs(True, gate.quiet(ok))
        padded = ok + b" " * (gate.MAX_INPUT - len(ok))
        self.assertIs(True, gate.quiet(padded))
        for value in (b"", b"not json", b"[]", b"null", ok + b" " * (gate.MAX_INPUT + 1 - len(ok)),
                      b'{"hook_event_name":"PreToolUse","tool_name":"Grep","tool_name":"Grep"}',
                      b'{"hook_event_name":"PreToolUse","tool_name":"Grep","n":NaN}',
                      b'{"hook_event_name":"PreToolUse","tool_name":"Gr\xffep"}', b"[" * 100_000,
                      raw({**event("Grep"), "tool_name": {}}), raw({k: v for k, v in event("Grep").items() if k != "tool_name"}),
                      "not bytes"):
            with self.subTest(value=value[:60]):
                self.assertIs(False, gate.quiet(value))

    def test_only_a_claude_event_run_reads_input_early(self):
        class Stdin:
            def __init__(self):
                self.buffer = io.BytesIO(b"payload")

        for argv in (["--client", "codex"], ["event", "--client", "codex"], ["doctor", "--client", "claude"],
                     ["--client=claude"], ["--client", "claude", "replay", "--input", "x"], []):
            with self.subTest(argv=argv), patch.object(sys, "stdin", Stdin()) as stdin:
                self.assertIsNone(gate.read(argv))
                self.assertEqual(0, stdin.buffer.tell())  # Left for the full path to read.
        for argv in (["--client", "claude"], ["event", "--client", "claude"]):
            with self.subTest(argv=argv), patch.object(sys, "stdin", Stdin()):
                self.assertEqual(b"payload", gate.read(argv))


class ParityTests(unittest.TestCase):
    """Whenever the gate answers, the full path answers {} and changes no stored record."""

    STORES = ("", "profile-boundaries", "skill-gate", "skill-note", "rerun-note")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.data = Path(temporary.name)
        self.environment = {"PLUGIN_DATA": str(self.data)}
        # Each store holds a live and an expired record, so even the expiry sweep of an opened
        # transaction shows as a change.
        for store in self.STORES:
            with PipelineStore(self.data / store, clock=lambda: NOW - 2_000).transaction() as tx:
                tx.put("seed", "expired", {"v": 1}, NOW - 1_000)
                tx.put("seed", "live", {"v": 2}, NOW + 1_000)
        # A transcript, named by its session's id as Claude names it, that already ran the shell
        # scenarios four times since the owner's message.
        self.transcript = self.data / "0f8fad5b-d9cb-469f-a165-70867728950e.jsonl"
        lines = [{"type": "user", "message": {"role": "user", "content": "run the checks"}, "uuid": "u1"}]
        for index in range(4):
            lines.append({"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": f"t{index}", "name": tool, "input": data}
                for tool, data in QUIET + FULL if tool in predicates.SHELLS and isinstance(data, dict)]}})
        self.transcript.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")

    def contents(self):
        rows = {}
        for path in sorted(self.data.rglob("routing-v2.sqlite3")):
            db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
            try:
                rows[path.parent.relative_to(self.data).as_posix()] = db.execute(
                    "SELECT kind, id, payload, expires FROM records ORDER BY kind, id").fetchall()
            finally:
                db.close()
        return rows

    def corpus(self):
        identities = ({"transcript_path": str(self.transcript)},
                      {"transcript_path": str(self.transcript), "agent_id": "a1", "agent_type": "general-purpose"},
                      {"agent_id": "a2", "agent_type": "assay:worker", "prompt_id": "p1"})
        for tool, data in QUIET + FULL:
            for number, identity in enumerate(identities):
                yield event(tool, data, tool_use_id=f"call-{number}", **identity)

    def test_the_full_path_answers_every_gated_call_with_nothing_and_records_nothing(self):
        before, answered = self.contents(), 0
        self.assertEqual({store or "." for store in self.STORES}, set(before))
        for item in self.corpus():
            if not gate.quiet(raw(item)):
                continue
            answered += 1
            with self.subTest(tool=item["tool_name"], data=item["tool_input"], agent=item.get("agent_id")):
                self.assertEqual(({}, None), cli.process(item, "claude", self.environment, clock=lambda: NOW))
                self.assertEqual(before, self.contents())
        self.assertEqual(len(QUIET) * 3, answered)

    def test_the_corpus_reaches_the_checks_and_the_gate_may_pass_more_than_they_answer(self):
        # Shows the oracle can fail: calls sent the full path do get notes, refusals or records.
        reached, passed_quietly = 0, 0
        for item in self.corpus():
            if gate.quiet(raw(item)):
                continue
            before = self.contents()
            result, error = cli.process(item, "claude", self.environment, clock=lambda: NOW)
            self.assertIsNone(error)
            if result or before != self.contents():
                reached += 1
            else:
                passed_quietly += 1  # The gate is a superset: this call needed no full path.
        self.assertGreater(reached, len(FULL))
        self.assertGreater(passed_quietly, 0)


class StoreTests(unittest.TestCase):
    """A Claude tool call that will record nothing opens no store transaction; Codex keeps its own."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.data = Path(temporary.name)
        self.rules, self.fingerprint = activation.load_rules(ROOT)
        self.opened = []
        original = PipelineStore.transaction

        def transaction(store):
            self.opened.append(Path(store.directory).name)
            return original(store)

        opened = patch.object(PipelineStore, "transaction", transaction)
        opened.start()
        self.addCleanup(opened.stop)

    def apply(self, client, item, context="", outcome=None):
        self.opened.clear()
        decision = state.apply(item, client, {"rule_ids": [], "context": context}, self.rules, self.fingerprint,
                               str(self.data), outcome=outcome, clock=lambda: NOW)
        return decision, list(self.opened)

    def test_a_claude_call_with_no_context_opens_no_transaction(self):
        item = event("Grep", tool_use_id="call-1", transcript_path="/logs/session-1.jsonl")
        self.assertEqual(({"rule_ids": [], "context": ""}, []), self.apply("claude", item))
        # A reply with context is recorded as delivered, and a guard keeps its transaction.
        self.assertEqual([self.data.name], self.apply("claude", item, context="note")[1])
        self.assertEqual([self.data.name], self.apply("claude", item, outcome="guard")[1])

    def test_a_codex_call_keeps_its_transaction_and_its_compaction_restore(self):
        item = event("exec", tool_use_id="call-1", transcript_path="/logs/rollout-1.jsonl")
        self.assertEqual([self.data.name], self.apply("codex", item)[1])
        rule = next(iter(self.rules))
        key = state.identity(item, "codex")
        with PipelineStore(self.data, clock=lambda: NOW).transaction() as tx:
            tx.put("hook-context", key, {"rules": [rule["id"]], "fingerprint": self.fingerprint,
                                         "pending_restore": True, "id": key, "at": NOW}, NOW + 100)
        decision, opened = self.apply("codex", {**item, "tool_use_id": "call-2"})
        self.assertIn("recheck relevance after compaction", decision["context"])
        self.assertEqual([self.data.name], opened)

    def test_a_claude_session_call_skips_the_profile_lookup_and_a_subagent_or_codex_call_keeps_it(self):
        worker = "11111111-2222-7333-8444-555555555555"
        boundaries = self.data / "profile-boundaries"
        with PipelineStore(boundaries, clock=lambda: NOW).transaction() as tx:
            for agent in (worker, "a1"):
                tx.put("profile", digest({"session": "session-1", "agent": agent}), {"role": "evidence-reviewer"},
                       NOW + 100)
        environment = {"PLUGIN_DATA": str(self.data)}
        top = event("Write", transcript_path="/logs/" + worker + ".jsonl")
        self.opened.clear()
        self.assertEqual({}, cli.reviewer_boundary(top, "claude", environment, clock=lambda: NOW))
        self.assertEqual([], self.opened)
        for client, item in (("codex", top), ("claude", event("Write", agent_id="a1"))):
            with self.subTest(client=client, agent=item.get("agent_id")):
                self.opened.clear()
                result = cli.reviewer_boundary(item, client, environment, clock=lambda: NOW)
                self.assertEqual("deny", result["hookSpecificOutput"]["permissionDecision"])
                self.assertEqual(["profile-boundaries"], self.opened)


class EntryTests(unittest.TestCase):
    """The real entry, run as the manifest runs it, in a fresh interpreter."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.environment = {**CLEAN, "PLUGIN_DATA": temporary.name}

    def run_entry(self, payload, client="claude"):
        program = ("import json, runpy, sys\n"
                   f"sys.argv = [{str(ENTRY)!r}, '--client', {client!r}]\n"
                   "code = 0\n"
                   "try:\n    runpy.run_path(sys.argv[0], run_name='__main__')\n"
                   "except SystemExit as exc:\n    code = exc.code\n"
                   f"print(json.dumps([code, sorted(set({list(HEAVY)!r}) & set(sys.modules))]), file=sys.stderr)\n")
        result = subprocess.run([sys.executable, "-I", "-B", "-c", program], input=payload, capture_output=True,
                                timeout=60, env=self.environment)
        lines = result.stderr.decode().splitlines()
        code, heavy = json.loads(lines[-1])
        return code, result.stdout, lines[:-1], heavy

    def test_a_gated_call_prints_the_empty_reply_without_loading_the_checks(self):
        code, stdout, errors, heavy = self.run_entry(raw(event("Grep", {"pattern": "x"})))
        self.assertEqual((0, [], []), (code, errors, heavy))
        # The same bytes the full path prints for an empty result.
        _, full, _, loaded = self.run_entry(raw(event("Read", {"file_path": "/work/skills/unknown-skill/SKILL.md"})))
        self.assertEqual(sorted(CHECKS), loaded)
        self.assertEqual(full, stdout)
        self.assertEqual(b"{}", stdout.strip())

    def test_a_call_the_gate_passes_reaches_the_full_path_with_its_input(self):
        code, stdout, errors, heavy = self.run_entry(raw(event("Edit", {"file_path": "/work/src/app.py"})))
        self.assertEqual((0, []), (code, errors))
        self.assertIn("assay:code-change", json.loads(stdout)["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(sorted(CHECKS), heavy)

    def test_invalid_input_fails_on_the_full_path_as_before(self):
        oversized = raw(event("Grep")) + b" " * gate.MAX_INPUT
        for payload in (b"", b"not json", oversized, b'{"hook_event_name":"PreToolUse","tool_name":"Grep","n":NaN}'):
            with self.subTest(payload=payload[:40]):
                code, stdout, errors, _ = self.run_entry(payload)
                self.assertEqual(1, code)
                self.assertEqual(b"", stdout)
                self.assertEqual(["Assay: invalid or unavailable hook input/configuration; no payload was recorded."],
                                 errors)

    def test_a_codex_call_always_takes_the_full_path(self):
        code, stdout, errors, heavy = self.run_entry(raw(event("Grep", transcript_path="/logs/rollout-1.jsonl")),
                                                     client="codex")
        self.assertEqual((0, b"{}", []), (code, stdout.strip(), errors))
        self.assertEqual(sorted(CHECKS), heavy)

    def test_an_event_run_reads_its_command_line_as_the_parser_does(self):
        for argv in cli.EVENT_RUNS:
            with self.subTest(argv=argv):
                built, parsed = cli.arguments(list(argv))
                self.assertIsNone(built)
                self.assertEqual(vars(cli.command_parser().parse_args(list(argv))), vars(parsed))
        for argv in (["--client", "claude", "--settings", "x.json"], ["doctor", "--client", "codex"],
                     ["--client=claude"]):
            with self.subTest(argv=argv):
                built, parsed = cli.arguments(argv)
                self.assertIsNotNone(built)
                self.assertEqual(vars(cli.command_parser().parse_args(argv)), vars(parsed))


if __name__ == "__main__":
    unittest.main()
