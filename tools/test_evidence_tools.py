"""Behavioral tests of the utilities, not evaluations of coding models."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from tools import command_receipt as cr
from tools import native_smoke as ns
from tools import quality_scope as qs
from tools import repro_check as repro


class ReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.outputs = self.root / "receipts"
        self.outputs.mkdir()
        (self.root / "input.txt").write_text("frozen", encoding="utf-8")

    def run_code(self, code: str, **kwargs):
        return cr.capture([sys.executable, "-B", "-c", code], cwd=self.root,
                          output_parent=self.outputs, inputs=["input.txt"], **kwargs)

    def test_failed_command_and_both_streams_remain_verifiable(self) -> None:
        packet, result = self.run_code("import sys; print('partial'); print('failed', file=sys.stderr); sys.exit(7)")
        self.assertEqual("failed", result["state"])
        self.assertEqual(7, result["exit_code"])
        self.assertEqual(b"partial\n", (packet / "stdout.bin").read_bytes().replace(b"\r\n", b"\n"))
        intent, stored = cr.verify(packet, result["manifest_sha256"])
        self.assertEqual(["input.txt"], list(intent["inputs_before"]))
        self.assertEqual("failed", stored["state"])
        (packet / "stderr.bin").write_bytes(b"removed error")
        with self.assertRaisesRegex(ValueError, "receipt drift"):
            cr.verify(packet, result["manifest_sha256"])

    def test_failed_launch_is_recorded_not_discarded(self) -> None:
        packet, result = cr.capture([str(self.root / "missing-executable")], cwd=self.root,
                                     output_parent=self.outputs, inputs=["input.txt"])
        self.assertEqual("launch-error", result["state"])
        self.assertIsNone(result["exit_code"])
        self.assertTrue(result["error"])
        cr.verify(packet, result["manifest_sha256"])

    def test_timeout_remains_non_success(self) -> None:
        packet, result = self.run_code("import time; print('started', flush=True); time.sleep(10)", timeout=0.2)
        self.assertEqual("timeout", result["state"])
        self.assertIn("descendants", result["effects"])
        cr.verify(packet, result["manifest_sha256"])

    def test_input_change_is_visible_even_with_exit_zero(self) -> None:
        _, result = self.run_code("from pathlib import Path; Path('input.txt').write_text('changed')")
        self.assertEqual("completed", result["state"])
        self.assertEqual(["input.txt"], result["changed_inputs"])
        self.assertEqual(125, repro.classify(result, b"ok", b"ok", b"bad"))

    def link_input(self) -> Path:
        selected = self.root / "selected.txt"
        try:
            selected.symlink_to("input.txt")
        except OSError as error:
            self.skipTest(f"host cannot create symlink: {error}")
        return selected

    def test_stable_aliases_remain_separate_selected_inputs(self) -> None:
        self.link_input()
        packet, result = cr.capture([sys.executable, "-c", "print('ok')"],
            cwd=self.root, output_parent=self.outputs, inputs=["selected.txt", "input.txt"])
        intent, stored = cr.verify(packet, result["manifest_sha256"])
        self.assertEqual({"selected.txt", "input.txt"}, set(intent["inputs_before"]))
        self.assertEqual(intent["inputs_before"], stored["inputs_after"])
        self.assertEqual([], stored["changed_inputs"])
        self.assertEqual(0, repro.classify(result, b"ok", b"ok", b"bad"))

    def test_retargeted_or_removed_alias_cannot_classify_as_good(self) -> None:
        selected = self.link_input()
        (self.root / "other.txt").write_text("changed", encoding="utf-8")
        for replacement in ("p.symlink_to('other.txt')", "p.symlink_to('missing.txt')", "pass"):
            with self.subTest(replacement=replacement):
                if selected.is_symlink():
                    selected.unlink()
                selected.symlink_to("input.txt")
                packet, result = cr.capture([sys.executable, "-c",
                    "from pathlib import Path; p=Path('selected.txt'); p.unlink(); "
                    + replacement + "; print('ok')"], cwd=self.root,
                    output_parent=self.outputs, inputs=["selected.txt"])
                self.assertEqual("completed", result["state"])
                self.assertEqual(["selected.txt"], result["changed_inputs"])
                self.assertEqual(125, repro.classify(result, b"ok", b"ok", b"bad"))
                cr.verify(packet, result["manifest_sha256"])

    def test_directory_alias_retarget_outside_cwd_is_unclassified(self) -> None:
        project = self.root / "project"
        source = project / "source"
        source.mkdir(parents=True)
        (source / "input.txt").write_text("frozen", encoding="utf-8")
        alias = project / "selected"
        try:
            alias.symlink_to("source", target_is_directory=True)
        except OSError as error:
            self.skipTest(f"host cannot create symlink: {error}")
        _, result = cr.capture([sys.executable, "-c",
            "from pathlib import Path; p=Path('selected'); p.unlink(); "
            "p.symlink_to('..', target_is_directory=True); print('ok')"],
            cwd=project, output_parent=self.outputs, inputs=["selected/input.txt"])
        self.assertEqual("completed", result["state"])
        self.assertEqual({"selected/input.txt": None}, result["inputs_after"])
        self.assertEqual(["selected/input.txt"], result["changed_inputs"])
        self.assertEqual(125, repro.classify(result, b"ok", b"ok", b"bad"))

    def test_invalid_arguments_do_not_allocate_receipts(self) -> None:
        for argv, inputs, timeout in (([], ["input.txt"], 1), ([sys.executable], [], 1),
                                      ([sys.executable], ["input.txt"], float("inf"))):
            with self.subTest(argv=argv, inputs=inputs), self.assertRaises(ValueError):
                cr.capture(argv, cwd=self.root, output_parent=self.outputs, inputs=inputs, timeout=timeout)
        self.assertEqual([], list(self.outputs.iterdir()))

    def test_receipt_is_not_verified_by_its_own_mutable_digest(self) -> None:
        packet, result = self.run_code("print('ok')")
        (packet / "manifest.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "retained digest"):
            cr.verify(packet, result["manifest_sha256"])


class NativeEventTests(unittest.TestCase):
    def trace(self, *, error: bool = False, terminal: bool = True) -> str:
        events = [{"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill", "id": "call-1", "input": {"skill": "test-audit"}}]}},
                  {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "call-1", "is_error": error, "content": "result"}]}}]
        if terminal:
            events.append({"type": "result", "is_error": False})
        return "\n".join(json.dumps(e) for e in events)

    def test_requires_successful_loader_event_not_model_statement(self) -> None:
        self.assertEqual("observed-loader-contract", ns.inspect_events(self.trace(), client="claude", required=("test-audit",))["status"])
        for text in (self.trace(error=True), self.trace(terminal=False),
                     json.dumps({"type": "assistant", "message": {"content": "I used test-audit"}})):
            with self.subTest(text=text):
                self.assertEqual("unverified", ns.inspect_events(text, client="claude", required=("test-audit",))["status"])

    def test_forbidden_attempt_counts_even_when_it_failed(self) -> None:
        result = ns.inspect_events(self.trace(error=True), client="claude", forbidden=("test-audit",))
        self.assertEqual("refuted", result["status"])
        self.assertEqual(["test-audit"], result["prohibited_attempts"])

    def test_failed_non_skill_call_remains_in_the_observed_record(self) -> None:
        records = [json.loads(line) for line in self.trace().splitlines()]
        records[0]["message"]["content"].append({"type": "tool_use", "name": "Read", "id": "read-1", "input": {"file_path": "missing.txt"}})
        records[1]["message"]["content"].append({"type": "tool_result", "tool_use_id": "read-1", "is_error": True, "content": "not found"})
        result = ns.inspect_events("\n".join(json.dumps(x) for x in records), client="claude", required=("test-audit",))
        self.assertEqual("observed-loader-contract", result["status"])
        self.assertEqual("Read", result["adverse_calls"][0]["tool"])
        self.assertEqual("failed", result["adverse_calls"][0]["outcome"])

    def test_codex_shell_mentions_are_not_fabricated_activation(self) -> None:
        text = '\n'.join(json.dumps(x) for x in [
            {"type": "item.completed", "item": {"type": "command_execution", "command": "cat skills/test-audit/SKILL.md", "exit_code": 0}},
            {"type": "turn.completed"}])
        self.assertEqual("unverified", ns.inspect_events(text, client="codex", required=("test-audit",))["status"])

    def test_truncated_and_duplicate_native_events_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ns.inspect_events('{"type":', client="claude")
        first = self.trace().splitlines()[0]
        with self.assertRaisesRegex(ValueError, "duplicate Skill"):
            ns.inspect_events(first + "\n" + self.trace(), client="claude")


# Controlled CLI stand-in exercises real subprocess/capture plumbing. This is
# not a real ESLint/TypeScript integration run and never claims to be one.
FAKE_TOOL = r'''
import json, sys
from pathlib import Path
a = sys.argv[1:]
if '--version' in a:
    print('fixture-tool-1')
elif '--print-config' in a:
    print(json.dumps({'rules': {'no-eval': [0 if Path(a[-1]).name == 'off.js' else 2]}}))
elif '--showConfig' in a:
    print(json.dumps({'files': ['good.js']}))
elif '--listFilesOnly' in a:
    print(str(Path('good.js').resolve()))
else:
    path = Path(a[-1]).resolve()
    messages = [{'ruleId': 'no-eval', 'severity': 2, 'message': 'forbidden'}] if path.name == 'bad.js' else []
    print(json.dumps([{'filePath': str(path), 'messages': messages}]))
    sys.exit(1 if messages else 0)
'''


class QualityScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.out = self.root / "receipts"
        self.out.mkdir()
        self.entry = self.root / "fixture_tool.py"
        self.entry.write_text(FAKE_TOOL, encoding="utf-8")
        for name in ("good.js", "bad.js", "off.js", "tsconfig.json"):
            (self.root / name).write_text("{}\n", encoding="utf-8")

    def probe(self, **kwargs):
        return qs.probe(node=sys.executable, entry=self.entry, root=self.root,
                        output_parent=self.out, inputs=["fixture_tool.py"], **kwargs)

    def test_rule_config_and_both_controls_are_observed(self) -> None:
        result = self.probe(kind="eslint", file="good.js", rule="no-eval", invalid="bad.js", valid="good.js")
        self.assertEqual("observed", result["status"])
        self.assertEqual("pass", result["control_detection"])
        self.assertTrue(result["receipts"])

    def test_disabled_rule_and_missing_selected_file_refute_scoped_claims(self) -> None:
        self.assertEqual("refuted", self.probe(kind="eslint", file="off.js", rule="no-eval")["status"])
        result = self.probe(kind="tsc", project="tsconfig.json", required_files=["good.js", "bad.js"])
        self.assertEqual("refuted", result["status"])
        self.assertEqual(["bad.js"], result["missing_required_files"])

    def test_file_selection_is_not_type_checking(self) -> None:
        result = self.probe(kind="tsc", project="tsconfig.json", required_files=["good.js"])
        self.assertEqual("selection-only", result["status"])
        self.assertIn("does not type-check", result["limits"])

    def test_parser_error_wrong_file_and_unrelated_diagnostic_do_not_prove_rule(self) -> None:
        path = (self.root / "bad.js").resolve()
        for record in ({"filePath": str(path), "messages": [{"fatal": True}]},
                       {"filePath": str(self.root / "good.js"), "messages": [{"ruleId": "no-eval", "severity": 2}]}):
            with self.subTest(record=record), self.assertRaises(ValueError):
                qs.diagnostic([record], file=path, rule="no-eval")
        self.assertFalse(qs.diagnostic([{"filePath": str(path), "messages": [{"ruleId": "other", "severity": 2}]}], file=path, rule="no-eval"))
        with self.assertRaises(ValueError):
            qs.severity(False)


class ReproducerTests(unittest.TestCase):
    def test_good_bad_and_unknown_are_distinct(self) -> None:
        result = {"state": "completed", "exit_code": 0, "changed_inputs": []}
        self.assertEqual(0, repro.classify(result, b"good", b"good", b"bad"))
        self.assertEqual(1, repro.classify(result, b"bad", b"good", b"bad"))
        self.assertEqual(125, repro.classify(result, b"other", b"good", b"bad"))
        for state in ("failed", "timeout", "launch-error"):
            self.assertEqual(125, repro.classify({**result, "state": state}, b"bad", b"good", b"bad"))
        with self.assertRaises(ValueError):
            repro.classify(result, b"same", b"same", b"same")


if __name__ == "__main__":
    unittest.main()
