"""Check the executable examples and fault controls, not a model's decisions."""
from __future__ import annotations

import csv
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
            (root / name).write_text(text, encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
