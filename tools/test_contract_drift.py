"""Contract-drift corpus and executable counterexamples; no model grading.

The deliberately limited fixture gates are subjects under review, not recommended
production implementations. Their observed results are checked against separately
specified cases below so a fixture cannot silently stop exhibiting its counterexample.
Generic refusals of the corpus and packet tools are tested once, in test_validation.py.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import eval_assets as ea

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "skills/code-change/evals"
CASES = EVALS / "contract-drift-cases.json"
RUBRIC = EVALS / "contract-drift-rubric.json"
METHODS = {"code-change", "implementation-planning", "independent-audit",
           "ui-delivery", "test-audit", "skill-evaluation"}


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


class DriftCorpusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = ea.load(CASES)
        self.rubric = ea.load(RUBRIC)

    def check_pair(self) -> None:
        with tempfile.TemporaryDirectory(prefix="drift-corpus-") as directory:
            root = Path(directory)
            write_json(root / "cases.json", self.cases)
            write_json(root / "rubric.json", self.rubric)
            ea.check_pair(root / "cases.json", root / "rubric.json", "code-change")

    def test_existing_pair_checker_accepts_corpus(self) -> None:
        self.check_pair()
        self.assertIn("code-change", ea.PAIRED_SKILLS)
        self.assertEqual(CASES.with_name(CASES.name.replace("-cases", "-rubric")), RUBRIC)

    def test_all_eighteen_families_have_two_distinct_inputs(self) -> None:
        by_id = {case["id"]: case for case in self.cases["cases"]}
        expected = {f"drift-{n:02d}-{v}" for n in range(1, 19) for v in ("a", "b")}
        self.assertEqual(set(by_id), expected)
        for number in range(1, 19):
            with self.subTest(family=number):
                a, b = (by_id[f"drift-{number:02d}-{v}"] for v in ("a", "b"))
                self.assertNotEqual(a["files"], b["files"])
                self.assertEqual(a["context"], b["context"])

    def test_grading_and_method_choices_are_not_input_fields(self) -> None:
        for case in self.cases["cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(set(case), {"id", "prompt", "context", "files"})
                ea.input_case(case)
                self.assertFalse(any("rubric" in name or "grading" in name
                                     for name in case["files"]))

    def test_rubrics_have_semantic_criteria_and_known_owners(self) -> None:
        seen_methods = set()
        for rubric in self.rubric["cases"]:
            with self.subTest(case=rubric["id"]):
                self.assertEqual(rubric["family"], "T" + rubric["id"].split("-")[1])
                self.assertTrue(rubric["methods"])
                self.assertLessEqual(set(rubric["methods"]), METHODS)
                seen_methods.update(rubric["methods"])
                for field in ("required_observations", "reject"):
                    self.assertTrue(rubric[field])
                    self.assertTrue(all(isinstance(item, str) and item.strip()
                                        for item in rubric[field]))
        self.assertEqual(seen_methods, METHODS)


class DriftFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.by_id = {case["id"]: case for case in ea.load(CASES)["cases"]}

    def observe(self, case_id: str) -> tuple[int, dict]:
        case = self.by_id[case_id]
        with tempfile.TemporaryDirectory(prefix="drift-fixture-") as directory:
            root = Path(directory)
            for name, content in case["files"].items():
                path = root / ea.portable(name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            result = subprocess.run([sys.executable, "-B", "check.py"], cwd=root,
                                    capture_output=True, text=True, encoding="utf-8",
                                    timeout=10, check=False)
            self.assertEqual(result.stderr, "", "A setup failure is not the intended diagnostic")
            self.assertIn(result.returncode, (0, 1))
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "pass" if result.returncode == 0 else "fail")
            self.assertEqual(before, {p.relative_to(root): p.read_bytes()
                                      for p in root.rglob("*") if p.is_file()})
            return result.returncode, report

    def state(self, number: int, variant: str) -> dict:
        return json.loads(self.by_id[f"drift-{number:02d}-{variant}"]["files"]["state.json"])

    def test_new_violation_inside_excepted_file_is_false_acceptance(self) -> None:
        self.assertEqual(self.observe("drift-08-a")[0], 0)
        self.assertEqual(len(self.state(8, "a")["violations"]), 2)
        self.assertEqual(self.state(8, "a")["excepted_files"], ["src/form.vue"])

    def test_known_interim_exception_remains_permitted(self) -> None:
        self.assertEqual(self.observe("drift-08-b")[0], 0)
        self.assertEqual([v["id"] for v in self.state(8, "b")["violations"]], ["control-a"])

    def test_equal_count_substitution_is_not_identity_preservation(self) -> None:
        state = self.state(9, "a")
        self.assertEqual(len(state["baseline"]), len(state["violations"]))
        self.assertNotEqual({v["id"] for v in state["baseline"]},
                            {v["id"] for v in state["violations"]})
        self.assertEqual(self.observe("drift-09-a")[0], 0)

    def test_legitimate_move_keeps_stable_object_identity(self) -> None:
        state = self.state(9, "b")
        self.assertNotEqual(state["baseline"][0]["file"], state["violations"][0]["file"])
        self.assertEqual(state["baseline"][0]["id"], state["violations"][0]["id"])
        self.assertEqual(self.observe("drift-09-b")[0], 0)

    def test_self_baseline_cannot_distinguish_authority(self) -> None:
        self.assertEqual(self.state(10, "a"), self.state(10, "b"))
        self.assertNotEqual(self.by_id["drift-10-a"]["files"]["contract.md"],
                            self.by_id["drift-10-b"]["files"]["contract.md"])
        self.assertEqual(self.observe("drift-10-a")[0], 0)
        self.assertEqual(self.observe("drift-10-b")[0], 0)

    def test_last_removal_is_false_rejection_not_missing_coverage(self) -> None:
        state = self.state(11, "a")
        self.assertEqual(state["baseline"], [])
        self.assertEqual(state["violations"], [])
        self.assertEqual(state["files_seen"], ["src/form.vue"])
        self.assertEqual(self.observe("drift-11-a")[0], 1)

    def test_intermediate_state_pass_does_not_prove_terminal_state(self) -> None:
        self.assertEqual(len(self.state(11, "b")["baseline"]), 1)
        self.assertEqual(self.observe("drift-11-b")[0], 0)

    def test_empty_scan_is_false_acceptance(self) -> None:
        code, report = self.observe("drift-12-a")
        self.assertEqual(code, 0)
        self.assertEqual(report["files_seen"], [])

    def test_empty_debt_after_real_scan_is_permitted(self) -> None:
        code, report = self.observe("drift-12-b")
        self.assertEqual(code, 0)
        self.assertEqual(report["files_seen"], ["src/form.vue"])


class DriftPacketTests(unittest.TestCase):
    def prepare(self, parent: Path, case_id: str = "drift-01-a", methods=()):
        return ea.prepare(cases_path=CASES, case_id=case_id, output_parent=parent,
                          skill_roots=tuple(ROOT / "skills" / name for name in methods), root=ROOT)

    def test_all_inputs_prepare_without_rubrics_or_coordinator_methods(self) -> None:
        with tempfile.TemporaryDirectory(prefix="drift-packets-") as directory:
            for case in ea.load(CASES)["cases"]:
                with self.subTest(case=case["id"]):
                    packet, digest = self.prepare(Path(directory), case["id"])
                    expected = {"prompt.txt", "context.txt", "manifest.json"}
                    expected.update("inputs/" + name for name in case["files"])
                    actual = {p.relative_to(packet).as_posix() for p in packet.rglob("*") if p.is_file()}
                    self.assertEqual(actual, expected)
                    self.assertEqual((packet / "prompt.txt").read_bytes(), (case["prompt"] + "\n").encode())
                    for name, text in case["files"].items():
                        self.assertEqual((packet / "inputs" / name).read_bytes(), text.encode())
                    self.assertEqual(ea.audit_tools(ROOT).verify_packet(packet, digest)["byte_integrity"], "pass")

    def test_explicit_multi_method_packet_excludes_all_evaluation_data(self) -> None:
        with tempfile.TemporaryDirectory(prefix="drift-methods-") as directory:
            parent = Path(directory)
            methods = ("code-change", "implementation-planning")
            packet, digest = self.prepare(parent, methods=methods)
            files = [p.relative_to(packet) for p in packet.rglob("*") if p.is_file()]
            self.assertFalse(any("evals" in p.parts for p in files))
            included = {p.parts[1] for p in files if p.parts[0] == "skill"}
            self.assertEqual(included, set(methods))
            manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["source_sha256"], hashlib.sha256(CASES.read_bytes()).hexdigest())
            ea.audit_tools(ROOT).verify_packet(packet, digest)

    def test_method_selection_does_not_change_task_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="drift-comparison-") as directory:
            parent = Path(directory)
            plain, _ = self.prepare(parent)
            treated, _ = self.prepare(parent, methods=("code-change",))
            for path in plain.rglob("*"):
                if path.is_file() and path.name != "manifest.json":
                    self.assertEqual(path.read_bytes(), (treated / path.relative_to(plain)).read_bytes())


if __name__ == "__main__":
    unittest.main()
