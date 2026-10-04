"""Check the executable examples and fault controls, not a model's decisions."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "skills/skill-evaluation/evals/workflow-execution-cases.json"


class WorkflowExecutionFixtures(unittest.TestCase):
    def materialize(self, case_id):
        cases = json.loads(CORPUS.read_text(encoding="utf-8"))["cases"]
        case = next(case for case in cases if case["id"] == case_id)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        for name, text in case["files"].items():
            (root / name).write_bytes(text.encode("utf-8"))
        return root

    def test_green_helper_does_not_establish_public_export(self):
        root = self.materialize("WX-01")
        unit = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover"],
                              cwd=root, capture_output=True, text=True, timeout=10)
        self.assertEqual(0, unit.returncode, unit.stderr)
        command = [sys.executable, "-B", "export.py", "sample.csv", "result.csv"]
        expected = [{"name": "amy", "note": "first"}, {"name": "Amy", "note": "second"},
                    {"name": "Zoe", "note": "a,b"}]
        def output():
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=10)
            self.assertEqual(0, result.returncode, result.stderr)
            with (root / "result.csv").open(newline="", encoding="utf-8") as stream:
                return list(csv.DictReader(stream))
        self.assertNotEqual(expected, output())
        source = root / "export.py"
        original = source.read_text(encoding="utf-8")
        self.assertEqual(1, original.count("writer.writerows(rows)"))
        source.write_text(original.replace("writer.writerows(rows)", "writer.writerows(ordered(rows))"), encoding="utf-8")
        self.assertEqual(expected, output())

    def test_authorization_fault_and_valid_neighbor(self):
        root = self.materialize("WX-03")
        source = root / "access.py"
        original = source.read_text(encoding="utf-8")
        broken = runpy.run_path(str(source))["delete_record"]
        records = [{"tenant": "two"}]
        broken(records, 0, "admin", "one")
        self.assertEqual([], records)
        self.assertEqual(1, original.count('role == "admin" or'))
        source.write_text(original.replace('role == "admin" or', 'role == "admin" and'), encoding="utf-8")
        repaired = runpy.run_path(str(source))["delete_record"]
        for role, actor, target in (("admin", "one", "two"), ("reader", "one", "one")):
            with self.subTest(role=role, actor=actor, target=target):
                records = [{"tenant": target}]
                with self.assertRaises(PermissionError):
                    repaired(records, 0, role, actor)
                self.assertEqual([{"tenant": target}], records)
        records = [{"tenant": "one"}]
        self.assertEqual({"tenant": "one"}, repaired(records, 0, "admin", "one"))
        self.assertEqual([], records)

    def test_different_setup_failures_leave_the_same_consumer_unreached(self):
        root = self.materialize("WX-04")
        command = [sys.executable, "-B", "report.py", "config.json"]
        def run():
            return subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=10)
        result = run()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("SyntaxError", result.stderr)
        self.assertFalse((root / "report.txt").exists())
        (root / "renderer.py").write_text(
            'def render(count, total):\n    return f"Orders: {count}; total: {total}\\n"\n',
            encoding="utf-8")
        result = run()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("FileNotFoundError", result.stderr)
        self.assertFalse((root / "report.txt").exists())
        config_path = root / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["input"] = "orders.csv"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        result = run()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("KeyError: 'value'", result.stderr)
        self.assertFalse((root / "report.txt").exists())
        source = root / "report.py"
        original = source.read_text(encoding="utf-8")
        source.write_text(original.replace('order["value"]', 'order["amount"]'), encoding="utf-8")
        result = run()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("Orders: 2; total: 15\n", result.stdout)
        self.assertEqual(result.stdout, (root / "report.txt").read_text(encoding="utf-8"))
        with (root / "orders.csv").open(newline="", encoding="utf-8") as stream:
            self.assertEqual([{"order": "first", "amount": "8"}, {"order": "second", "amount": "7"}],
                             list(csv.DictReader(stream)))

    def test_continuation_has_an_applicable_result_and_a_stale_narrow_one(self):
        root = self.materialize("WX-05")
        checks = json.loads((root / "CHECKS.json").read_text(encoding="utf-8"))["checks"]
        def mismatches(check):
            return [name for name, expected in check["inputs"].items()
                    if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected]
        self.assertEqual([], mismatches(checks[0]))
        self.assertEqual(["report.py"], mismatches(checks[1]))
        for check in checks:
            result = subprocess.run([sys.executable, *check["argv"][1:]], cwd=root,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(0, result.returncode, result.stderr)
        old_report = 'from totals import subtotal\n\ndef report(values):\n    return "USD " + str(subtotal(values))\n'
        self.assertEqual(checks[1]["inputs"]["report.py"], hashlib.sha256(old_report.encode()).hexdigest())
        source = root / "report.py"
        current = source.read_bytes()
        source.write_bytes(old_report.encode("utf-8"))
        prefix = subprocess.run([sys.executable, *checks[1]["argv"][1:]], cwd=root,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(0, prefix.returncode, prefix.stderr)
        command = [sys.executable, "-B", "-c",
                   "from report import report; print(report([8, 7])); print(report([]))"]
        faulty = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=10)
        self.assertEqual(0, faulty.returncode, faulty.stderr)
        self.assertNotEqual("USD 15.00\nUSD 0.00\n", faulty.stdout)
        source.write_bytes(current)
        repaired = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=10)
        self.assertEqual(0, repaired.returncode, repaired.stderr)
        self.assertEqual("USD 15.00\nUSD 0.00\n", repaired.stdout)


if __name__ == "__main__":
    unittest.main()
