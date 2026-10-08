"""Calibration: protected faults are rejected and supported alternatives pass.

These are constructed evaluator controls, never subject-trial outcomes.
Run with: python -B -m unittest discover -s skills/skill-evaluation/evals -p test_comparison_checks.py
"""

import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import comparison_checks as checks


PUBLIC_REGRESSION = '''import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

class PublicRegression(unittest.TestCase):
    def test_public_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "in.csv"
            destination = Path(temporary) / "out.csv"
            source.write_text('name,note,id\\nZoe,"a,b",1\\namy,first,2\\nAmy,second,3\\n', encoding="utf-8")
            completed = subprocess.run([sys.executable, "-B", "export.py", str(source), str(destination)], capture_output=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            with destination.open(newline="", encoding="utf-8") as stream:
                actual = list(csv.reader(stream))
            self.assertEqual(actual, [["name", "note", "id"], ["amy", "first", "2"], ["Amy", "second", "3"], ["Zoe", "a,b", "1"]])
'''

DIRECT_REGRESSION = '''from export import export
import csv
from pathlib import Path
import tempfile
import unittest
class DirectRegression(unittest.TestCase):
    def test_public_export(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, output = Path(temporary)/"in.csv", Path(temporary)/"out.csv"
            source.write_text("name,id\\nZoe,1\\namy,2\\n", encoding="utf-8")
            export(source, output)
            with output.open(newline="", encoding="utf-8") as stream:
                self.assertEqual(list(csv.reader(stream)), [["name", "id"], ["amy", "2"], ["Zoe", "1"]])
'''


class ComparisonCalibration(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="assay-comparison-calibration-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def fixture(self, case_id):
        work = self.root / case_id
        work.mkdir()
        for name, text in checks.load_cases()[case_id]["files"].items():
            path = work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        (work / "answer.md").write_text("Calibration artifact; no subject run took place.\n", encoding="utf-8")
        return work

    def statuses(self, case_id, work):
        result = checks.evaluate(case_id, work)
        self.assertTrue(result["evaluator_preserved_subject_bytes"])
        return {row["id"]: row["status"] for row in result["criteria"]}, result

    def test_original_fault_is_not_green(self):
        statuses, result = self.statuses("B1-M", self.fixture("B1-M"))
        self.assertEqual(statuses["B1-M-1"], "refuted")
        self.assertEqual(statuses["B1-M-4"], "refuted")
        self.assertEqual(statuses["B1-M-5"], "refuted")
        self.assertEqual(statuses["B1-M-7"], "met")
        self.assertEqual(statuses["B1-M-8"], "not_verified")
        self.assertEqual(result["evidence"]["public_csv"]["returncode"], 0)

    def test_repaired_code_with_real_command_regression(self):
        work = self.fixture("B1-M")
        (work / "export.py").write_text(checks.fixture_export("repaired"), encoding="utf-8")
        (work / "test_public.py").write_text(PUBLIC_REGRESSION, encoding="utf-8")
        statuses, result = self.statuses("B1-M", work)
        for n in range(1, 8):
            self.assertEqual(statuses[f"B1-M-{n}"], "met", (n, result))
        self.assertEqual(statuses["B1-M-8"], "not_verified")
        bad = result["evidence"]["unittest_controls"]["original_fault"]["receipt"]
        self.assertTrue(bad["failures"])
        self.assertFalse(bad["errors"])
        self.assertEqual(result["evidence"]["submitted_suite_assessment"]["status"], "met")

    def test_three_row_sort_fault_is_refuted_despite_passing_controls(self):
        work = self.fixture("B1-M")
        faulty = checks.fixture_export("repaired").replace(
            'return sorted(rows, key=lambda row: row["name"].casefold())',
            'return sorted(rows, key=lambda row: row["name"].casefold(), reverse=len(rows) == 3)')
        (work / "export.py").write_text(faulty, encoding="utf-8")
        (work / "test_public.py").write_text(PUBLIC_REGRESSION, encoding="utf-8")
        statuses, result = self.statuses("B1-M", work)
        self.assertEqual(statuses["B1-M-1"], "refuted")
        self.assertEqual(result["status"], "refuted")
        for n in range(2, 8):
            self.assertEqual(statuses[f"B1-M-{n}"], "met", (n, result))
        self.assertEqual(result["evidence"]["sample_csv"]["parsed_output"], [
            ["name", "note", "id"], ["Zoe", "a,b", "1"], ["amy", "first", "2"], ["Amy", "second", "3"]])
        submitted = result["evidence"]["unittest_controls"]["submitted"]["receipt"]
        self.assertEqual(len(submitted["failures"]), 1)
        self.assertFalse(submitted["errors"])
        assessment = result["evidence"]["submitted_suite_assessment"]
        self.assertEqual(assessment["kind"], "assertion_failures")
        self.assertEqual(assessment["status"], "refuted")
        self.assertEqual(assessment["independently_refuted_criteria"], ["B1-M-1"])

    def test_unprobed_input_failure_remains_an_unresolved_assertion(self):
        work = self.fixture("B1-M")
        faulty = checks.fixture_export("repaired").replace(
            'return sorted(rows, key=lambda row: row["name"].casefold())',
            'return sorted(rows, key=lambda row: row["name"].casefold(), reverse=len(rows) == 4)')
        four_row_regression = PUBLIC_REGRESSION.replace(
            'Amy,second,3\\n', 'Amy,second,3\\nBob,normal,4\\n').replace(
            '["Amy", "second", "3"], ["Zoe", "a,b", "1"]',
            '["Amy", "second", "3"], ["Bob", "normal", "4"], ["Zoe", "a,b", "1"]')
        (work / "export.py").write_text(faulty, encoding="utf-8")
        (work / "test_public.py").write_text(four_row_regression, encoding="utf-8")
        statuses, result = self.statuses("B1-M", work)
        for n in range(1, 8):
            self.assertEqual(statuses[f"B1-M-{n}"], "met", (n, result))
        assessment = result["evidence"]["submitted_suite_assessment"]
        self.assertEqual(assessment["status"], "not_verified")
        self.assertEqual(assessment["kind"], "assertion_failures")
        self.assertEqual(assessment["assertion_failures"], 1)
        self.assertEqual(assessment["test_errors"], 0)
        self.assertEqual(assessment["independently_refuted_criteria"], [])

    def test_unresolved_assessment_caps_command_acceptance(self):
        work = self.fixture("B1-M")

        def otherwise_met(work, results, evidence):
            for item in results.values():
                item["status"] = "met"
            evidence["submitted_suite_assessment"] = {
                "status": "not_verified", "kind": "assertion_failures"}

        output = io.StringIO()
        with patch.object(checks, "check_b1_main", otherwise_met), patch.object(
                sys, "argv", ["comparison_checks.py", "--case", "B1-M", "--work", str(work)]):
            with contextlib.redirect_stdout(output):
                exit_code = checks.main()
        result = json.loads(output.getvalue())
        self.assertEqual({item["status"] for item in result["criteria"]}, {"met"})
        self.assertEqual(result["status"], "not_verified")
        self.assertEqual(exit_code, 2)

    def test_inline_valid_alternative_and_direct_public_api_test(self):
        work = self.fixture("B1-M")
        (work / "export.py").write_text(checks.fixture_export("inline"), encoding="utf-8")
        (work / "test_direct.py").write_text(DIRECT_REGRESSION, encoding="utf-8")
        statuses, result = self.statuses("B1-M", work)
        for n in range(1, 8):
            self.assertEqual(statuses[f"B1-M-{n}"], "met", (n, result))
        self.assertEqual(result["evidence"]["submitted_suite_assessment"]["status"], "met")

    def test_in_place_sort_and_equivalent_csv_quoting_are_accepted(self):
        work = self.fixture("B1-M")
        alternative = checks.fixture_export("original").replace(
            "writer.writerows(rows)",
            'rows.sort(key=lambda item: item["name"].casefold())\n        writer.writerows(rows)').replace(
            "csv.DictWriter(stream, fieldnames=fields)",
            "csv.DictWriter(stream, fieldnames=fields, quoting=csv.QUOTE_ALL)")
        (work / "export.py").write_text(alternative, encoding="utf-8")
        (work / "test_public.py").write_text(PUBLIC_REGRESSION, encoding="utf-8")
        statuses, result = self.statuses("B1-M", work)
        for n in range(1, 8):
            self.assertEqual(statuses[f"B1-M-{n}"], "met", (n, result))
        self.assertEqual(result["evidence"]["submitted_suite_assessment"]["status"], "met")

    def test_bad_structure_assertion_does_not_refute_valid_public_behavior(self):
        work = self.fixture("B1-M")
        alternative = checks.fixture_export("inline").replace(
            "writer =", "output_writer =").replace("writer.", "output_writer.")
        (work / "export.py").write_text(alternative, encoding="utf-8")
        (work / "test_public.py").write_text(PUBLIC_REGRESSION, encoding="utf-8")
        (work / "test_structure.py").write_text(
            'from export import export\nimport unittest\n'
            'class Structure(unittest.TestCase):\n    def test_local_name(self):\n'
            '        self.assertIn("writer", export.__code__.co_varnames)\n', encoding="utf-8")
        statuses, result = self.statuses("B1-M", work)
        for n in range(1, 8):
            self.assertEqual(statuses[f"B1-M-{n}"], "met", (n, result))
        assessment = result["evidence"]["submitted_suite_assessment"]
        self.assertEqual(assessment["kind"], "assertion_failures")
        self.assertEqual(assessment["status"], "not_verified")
        self.assertEqual(assessment["independently_refuted_criteria"], [])

    def test_decoy_public_smoke_does_not_detect_original_fault(self):
        work = self.fixture("B1-M")
        (work / "export.py").write_text(checks.fixture_export("repaired"), encoding="utf-8")
        weak = DIRECT_REGRESSION.replace(
            'self.assertEqual(list(csv.reader(stream)), [["name", "id"], ["amy", "2"], ["Zoe", "1"]])',
            'self.assertEqual(len(list(csv.reader(stream))), 3)')
        (work / "test_smoke.py").write_text(weak, encoding="utf-8")
        statuses, _ = self.statuses("B1-M", work)
        self.assertEqual(statuses["B1-M-1"], "met")
        self.assertEqual(statuses["B1-M-4"], "met")
        self.assertEqual(statuses["B1-M-5"], "refuted")

    def test_setup_error_is_not_fault_detection(self):
        work = self.fixture("B1-M")
        (work / "export.py").write_text(checks.fixture_export("repaired"), encoding="utf-8")
        (work / "test_broken.py").write_text("import deliberately_missing_dependency\n", encoding="utf-8")
        statuses, result = self.statuses("B1-M", work)
        self.assertEqual(statuses["B1-M-5"], "not_verified")
        self.assertEqual(statuses["B1-M-7"], "not_verified")
        assessment = result["evidence"]["submitted_suite_assessment"]
        self.assertEqual(assessment["kind"], "test_errors")
        self.assertEqual(assessment["assertion_failures"], 0)
        self.assertEqual(assessment["test_errors"], 1)

    def test_skipped_suite_is_not_acceptance_evidence(self):
        work = self.fixture("B1-M")
        (work / "export.py").write_text(checks.fixture_export("repaired"), encoding="utf-8")
        (work / "test_export.py").write_text(
            'import unittest\n@unittest.skip("No operation is exercised")\n'
            'class Skipped(unittest.TestCase):\n    def test_nothing(self):\n        self.fail("unreached")\n',
            encoding="utf-8")
        statuses, _ = self.statuses("B1-M", work)
        self.assertEqual(statuses["B1-M-5"], "not_verified")
        self.assertEqual(statuses["B1-M-7"], "not_verified")

    def test_nonunicode_sort_is_rejected(self):
        work = self.fixture("B1-M")
        (work / "export.py").write_text(checks.fixture_export("inline").replace(".casefold()", ".lower()"), encoding="utf-8")
        statuses, _ = self.statuses("B1-M", work)
        self.assertEqual(statuses["B1-M-1"], "refuted")
        self.assertEqual(statuses["B1-M-2"], "refuted")

    def test_typo_fix_preserves_source_and_detects_extra_test(self):
        work = self.fixture("B1-C")
        original = (work / "README.md").read_text()
        (work / "README.md").write_text(original.replace("succesful", "successful"), encoding="utf-8")
        statuses, _ = self.statuses("B1-C", work)
        for n in (1, 2, 3):
            self.assertEqual(statuses[f"B1-C-{n}"], "met")
        (work / "test_unrequested.py").write_text("", encoding="utf-8")
        statuses, _ = self.statuses("B1-C", work)
        self.assertEqual(statuses["B1-C-3"], "refuted")

    def test_label_only_and_equivalent_html_serialization(self):
        work = self.fixture("B4-C")
        statuses, _ = self.statuses("B4-C", work)
        self.assertEqual(statuses["B4-C-1"], "refuted")
        changed = (work / "index.html").read_text().replace("Export chosen", "Export selected")
        # Attribute quoting and order are not a behavior or layout contract.
        changed = changed.replace('<button id="export" onclick=', '<button id=export onclick=')
        (work / "index.html").write_text(changed, encoding="utf-8")
        statuses, result = self.statuses("B4-C", work)
        for n in (1, 2, 3):
            self.assertEqual(statuses[f"B4-C-{n}"], "met")
        self.assertFalse(result["evidence"]["html_preservation"]["browser_executed"])
        self.assertEqual(statuses["B4-C-4"], "not_verified")

    def test_added_control_and_changed_handler_do_not_get_preservation_credit(self):
        work = self.fixture("B4-C")
        text = (work / "index.html").read_text().replace("Export chosen", "Export selected").replace("='r1'", "='r2'")
        text = text.replace("</html>", "<button>Extra</button></html>")
        (work / "index.html").write_text(text, encoding="utf-8")
        statuses, _ = self.statuses("B4-C", work)
        self.assertEqual(statuses["B4-C-2"], "not_verified")
        self.assertEqual(statuses["B4-C-3"], "refuted")

    def test_unimplemented_browser_case_never_reports_runtime_success(self):
        statuses, result = self.statuses("B4-M", self.fixture("B4-M"))
        self.assertEqual(set(statuses.values()), {"not_verified"})
        self.assertEqual(result["evidence"], {})


if __name__ == "__main__":
    unittest.main()
