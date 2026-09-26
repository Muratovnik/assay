"""Research-driven-change registration and frozen inputs, not model grading.

Use the existing native-plan, case-pair and packet mechanisms. These checks
establish integration and input integrity, not workflow execution or savings.
"""
from __future__ import annotations

import copy
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

from tools import assay as aa
from tools import eval_assets as ea

ROOT = Path(__file__).resolve().parents[1]
NAME = "research-driven-change"
SKILL = ROOT / "skills" / NAME
CASES = SKILL / "evals/cases.json"
RUBRIC = SKILL / "evals/rubric.json"


def hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def runtime_paths(root: Path) -> set[str]:
    paths = [root / "SKILL.md", *(root / "references").rglob("*")]
    paths += list((root / "agents").glob("openai.yaml"))
    return {p.relative_to(root).as_posix() for p in paths if p.is_file()}


class ResearchChangeIntegrationTests(unittest.TestCase):
    def test_native_registration_and_topology(self) -> None:
        catalog = aa.load_catalog(ROOT)
        assets = [a for a in catalog.assets if a.id == f"skill/{NAME}"]
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0].activation, "automatic")
        self.assertEqual(assets[0].path, f"skills/{NAME}")
        with tempfile.TemporaryDirectory(prefix="rdc-native-") as directory:
            home = Path(directory).resolve()
            entries = [e for e in aa.native_plan(ROOT, home)
                       if e.asset_id == f"skill/{NAME}"]
            self.assertEqual(len(entries), 2)
            actual = {(e.client, e.source, e.target, e.mode) for e in entries}
            self.assertEqual(actual, {
                ("codex", SKILL, home / ".agents/skills" / NAME, "link"),
                ("claude", home / ".agents/skills" / NAME,
                 home / ".claude/skills" / NAME, "link"),
            })
            self.assertFalse((home / ".agents").exists(), "Planning must not install")
            self.assertFalse((home / ".claude").exists())

    def test_corpus_registered_and_grading_is_separate(self) -> None:
        self.assertEqual(ea.PAIRED_SKILLS.count(NAME), 1)
        ea.check_pair(CASES, RUBRIC, NAME)
        cases, rubric = ea.load(CASES), ea.load(RUBRIC)
        self.assertEqual(set(cases), {"schema_version", "skill_name", "cases", "discovery_cases"})
        for collection, fields in (("cases", ("required", "reject")),
                                   ("discovery_cases", ("expected_methods", "avoid"))):
            for case in cases[collection]:
                with self.subTest(collection=collection, case=case["id"]):
                    self.assertEqual(ea.input_case(case), case)
                    self.assertFalse(set(fields) & set(case))
            for entry in rubric[collection]:
                for field in fields:
                    self.assertIsInstance(entry[field], list)
                    self.assertTrue(entry[field])
                    self.assertTrue(all(isinstance(value, str) and value.strip()
                                        for value in entry[field]))
        self.assertTrue({"RDC-01-plan", "RDC-02-adapter", "RDC-03-skill",
                         "RDC-15-lost-receipt", "RDC-16-ambiguous-receipt",
                         "RDC-17-new-revision", "RDC-18-draft-control",
                         "RDC-25-delivered-chain", "RDC-26-empty-checks"}
                        <= {case["id"] for case in cases["cases"]})

    def test_adapter_fixture_distinguishes_defect_and_valid_control(self) -> None:
        # Exercise the fixture oracle, not a model or the skill's effectiveness.
        case = next(c for c in ea.load(CASES)["cases"] if c["id"] == "RDC-02-adapter")
        original = case["files"]["adapter.py"]
        variants = (
            ("original defect", original, 1, "FAILED (failures=3)"),
            ("valid exact alias", original.replace("return name.lower()",
                                                  "return ALIASES.get(name, name)"), 0, "OK"),
            ("overbroad normalization", original.replace("return name.lower()",
                                                       "return ALIASES.get(name, name.lower())"),
             1, "FAILED (failures=2)"),
        )
        before = hashes(SKILL)
        with tempfile.TemporaryDirectory(prefix="rdc-oracle-") as directory:
            for index, (label, candidate, code, diagnostic) in enumerate(variants):
                with self.subTest(variant=label):
                    working = Path(directory) / str(index)
                    working.mkdir()
                    (working / "adapter.py").write_text(candidate, encoding="utf-8")
                    (working / "test_adapter.py").write_text(case["files"]["test_adapter.py"],
                                                          encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-B", "-E", "-s", "-m", "unittest", "test_adapter.py"],
                        cwd=working, capture_output=True, text=True, timeout=30,
                    )
                    self.assertEqual(result.returncode, code, result.stdout + result.stderr)
                    self.assertIn("Ran 3 tests", result.stderr)
                    self.assertIn(diagnostic, result.stderr)
        self.assertEqual(hashes(SKILL), before)

    def test_grading_field_is_rejected_with_valid_control(self) -> None:
        valid = copy.deepcopy(ea.load(CASES)["cases"][0])
        self.assertEqual(ea.input_case(valid), valid)
        with self.assertRaisesRegex(ValueError, "grading data"):
            ea.input_case(valid | {"required": ["evaluator-only answer"]})
        self.assertNotIn("required", valid)

    def test_runtime_links_and_fragments_resolve_without_evaluation_keys(self) -> None:
        for path in [SKILL / "SKILL.md", *(SKILL / "references").glob("*.md")]:
            for target in aa.MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
                if target.startswith(("https://", "http://", "mailto:")):
                    continue
                relative, _, fragment = target.partition("#")
                linked = (path.parent / relative).resolve() if relative else path
                linked.relative_to(ROOT)
                self.assertTrue(linked.is_file(), f"{path.name}: {target}")
                self.assertNotIn("evals", linked.relative_to(ROOT).parts)
                if fragment:
                    # Linked headings are ASCII, unique and punctuation-free here.
                    headings = re.findall(r"^#{1,6}\s+(.+)$",
                                          linked.read_text(encoding="utf-8"), re.MULTILINE)
                    anchors = {re.sub(r"[^\w -]", "", h.lower()).replace(" ", "-")
                               for h in headings}
                    self.assertIn(fragment, anchors, f"{path.name}: {target}")

    def test_consumers_return_to_transition_owner(self) -> None:
        for name, destination in (
            ("evidence-research", "stage-handoffs.md"),
            ("implementation-planning", "stage-handoffs.md"),
            ("code-maintenance", "stage-handoffs.md"),
            ("skill-design", "stage-handoffs.md"),
            ("independent-audit", "review-and-delivery.md"),
        ):
            with self.subTest(consumer=name):
                path = ROOT / "skills" / name / "SKILL.md"
                targets = {(path.parent / target.split("#", 1)[0]).resolve()
                           for target in aa.MARKDOWN_LINK.findall(path.read_text(encoding="utf-8"))
                           if NAME in target}
                self.assertIn(SKILL / "references" / destination, targets)


class ResearchChangePacketTests(unittest.TestCase):
    def prepare(self, parent: Path, case_id: str = "RDC-02-adapter", **kwargs):
        return ea.prepare(cases_path=CASES, case_id=case_id,
                          output_parent=parent, root=ROOT, **kwargs)

    def test_every_case_contains_exactly_its_own_inputs(self) -> None:
        before = hashes(SKILL)
        with tempfile.TemporaryDirectory(prefix="rdc-inputs-") as directory:
            parent = Path(directory).resolve()
            for collection, cases in ea.collections(ea.load(CASES)).items():
                for case in cases:
                    with self.subTest(collection=collection, case=case["id"]):
                        packet, digest = self.prepare(parent, case["id"], collection=collection)
                        expected = {"prompt.txt", "manifest.json"}
                        if "context" in case:
                            expected.add("context.txt")
                        expected.update("inputs/" + name for name in case.get("files", {}))
                        self.assertEqual(set(hashes(packet)), expected)
                        self.assertEqual((packet / "prompt.txt").read_text(encoding="utf-8"),
                                         case["prompt"] + "\n")
                        for name, value in case.get("files", {}).items():
                            self.assertEqual((packet / "inputs" / name).read_bytes(),
                                             value.encode("utf-8"))
                        self.assertEqual(ea.audit_tools(ROOT).verify_packet(packet, digest)
                                         ["byte_integrity"], "pass")
        self.assertEqual(hashes(SKILL), before)

    def test_two_consumers_receive_only_explicit_methods(self) -> None:
        with tempfile.TemporaryDirectory(prefix="rdc-consumers-") as directory:
            for name, case_id in (("code-maintenance", "RDC-02-adapter"),
                                  ("skill-design", "RDC-03-skill")):
                with self.subTest(consumer=name):
                    methods = (SKILL, ROOT / "skills" / name)
                    before = [hashes(method) for method in methods]
                    packet, digest = self.prepare(Path(directory).resolve(), case_id,
                                                  skill_roots=methods)
                    self.assertEqual({p.name for p in (packet / "skill").iterdir()},
                                     {NAME, name})
                    for method in methods:
                        frozen = packet / "skill" / method.name
                        self.assertEqual(set(hashes(frozen)), runtime_paths(method))
                        for relative in runtime_paths(method):
                            self.assertEqual((method / relative).read_bytes(),
                                             (frozen / relative).read_bytes())
                    self.assertFalse(any("evals" in p.relative_to(packet).parts
                                         for p in packet.rglob("*")))
                    self.assertEqual(ea.audit_tools(ROOT).verify_packet(packet, digest)
                                     ["byte_integrity"], "pass")
                    self.assertEqual([hashes(method) for method in methods], before)

    def test_optional_method_does_not_change_task_inputs(self) -> None:
        # Packet identity check only, not a behavioral baseline/candidate comparison.
        with tempfile.TemporaryDirectory(prefix="rdc-pair-") as directory:
            parent = Path(directory).resolve()
            for case_id in ("RDC-02-adapter", "RDC-03-skill"):
                with self.subTest(case=case_id):
                    plain, _ = self.prepare(parent, case_id)
                    candidate, _ = self.prepare(parent, case_id, skill_roots=(SKILL,))
                    self.assertEqual(hashes(plain / "inputs"), hashes(candidate / "inputs"))
                    for name in ("prompt.txt", "context.txt"):
                        self.assertEqual((plain / name).read_bytes(),
                                         (candidate / name).read_bytes())
                    self.assertFalse((plain / "skill").exists())
                    self.assertEqual({p.name for p in (candidate / "skill").iterdir()}, {NAME})

    def test_local_execution_cases_have_complete_subjects(self) -> None:
        # Packaging coverage: these tasks require edits, not hypothetical advice.
        subjects = {
            "RDC-02-adapter": {"adapter.py", "test_adapter.py", "research.md", "plan.md"},
            "RDC-03-skill": {"method/SKILL.md", "research.md", "plan.md"},
            "RDC-06-resume-valid": {"adapter.py", "test_adapter.py", "research.md", "plan.md"},
            "RDC-10-review-defect": {"adapter.py", "test_adapter.py", "research.md", "plan.md"},
        }
        records = {case["id"]: case for case in ea.load(CASES)["cases"]}
        for case_id, expected in subjects.items():
            with self.subTest(case=case_id):
                self.assertEqual(set(records[case_id].get("files", {})), expected)
                self.assertTrue(all(records[case_id]["files"].values()))

    def test_authorized_working_copy_preserves_frozen_evidence(self) -> None:
        # Exercise the documented coordinator setup, not model behavior.
        edits = {
            "RDC-02-adapter": ("adapter.py", "return name.lower()",
                               "return ALIASES.get(name, name)"),
            "RDC-03-skill": ("method/SKILL.md",
                             "Always discard existing research and start a new survey before any answer.",
                             "Reuse sufficient research; refresh materially changed premises."),
            "RDC-06-resume-valid": ("adapter.py", "ALIASES.get(name, name.lower())",
                                    "ALIASES.get(name, name)"),
            "RDC-10-review-defect": ("adapter.py", "ALIASES.get(name, name.lower())",
                                     "ALIASES.get(name, name)"),
        }
        with tempfile.TemporaryDirectory(prefix="rdc-editable-") as directory:
            parent = Path(directory).resolve()
            for case_id, (relative, old, new) in edits.items():
                with self.subTest(case=case_id):
                    packet, digest = self.prepare(parent, case_id, skill_roots=(SKILL,))
                    workspace = parent / case_id
                    before = hashes(packet)
                    shutil.copytree(packet / "inputs", workspace)
                    self.assertEqual(hashes(packet / "inputs"), hashes(workspace))
                    target = workspace / relative
                    original = target.read_text(encoding="utf-8")
                    self.assertEqual(original.count(old), 1)
                    target.write_text(original.replace(old, new), encoding="utf-8")
                    self.assertNotEqual(target.read_bytes(),
                                        (packet / "inputs" / relative).read_bytes())
                    if relative == "adapter.py":
                        result = self.run_fixture(workspace)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(hashes(packet), before)
                    self.assertEqual(ea.audit_tools(ROOT).verify_packet(packet, digest)
                                     ["byte_integrity"], "pass")
                    changed = {name for name, value in hashes(workspace).items()
                               if value != hashes(packet / "inputs").get(name)}
                    self.assertEqual(changed, {relative})

    def test_editing_frozen_input_is_still_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="rdc-frozen-") as directory:
            parent = Path(directory).resolve()
            packet, digest = self.prepare(parent)
            control, retained = self.prepare(parent)
            target = packet / "inputs/adapter.py"
            target.write_text(target.read_text(encoding="utf-8").replace(
                "return name.lower()", "return ALIASES.get(name, name)"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Packet drift"):
                ea.audit_tools(ROOT).verify_packet(packet, digest)
            self.assertEqual(ea.audit_tools(ROOT).verify_packet(control, retained)
                             ["byte_integrity"], "pass")

    @staticmethod
    def run_fixture(workspace: Path, *modules: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-B", "-E", "-s", "-m", "unittest",
             *(modules or ("test_adapter.py",))],
            cwd=workspace, capture_output=True, text=True, timeout=30,
        )

    def test_review_fixture_exposes_defect_hidden_by_green_original_suite(self) -> None:
        with tempfile.TemporaryDirectory(prefix="rdc-review-oracle-") as directory:
            parent = Path(directory).resolve()
            packet, digest = self.prepare(parent, "RDC-10-review-defect")
            workspace = parent / "work"
            shutil.copytree(packet / "inputs", workspace)
            original = self.run_fixture(workspace)
            self.assertEqual(original.returncode, 0, original.stdout + original.stderr)
            # Coordinator probe, never inserted into the executor's frozen inputs.
            contract = next(case for case in ea.load(CASES)["cases"]
                            if case["id"] == "RDC-02-adapter")["files"]["test_adapter.py"]
            (workspace / "test_contract.py").write_text(contract, encoding="utf-8")
            failed = self.run_fixture(workspace, "test_adapter.py", "test_contract.py")
            self.assertEqual(failed.returncode, 1, failed.stdout + failed.stderr)
            self.assertIn("test_unknown_identifier", failed.stderr)
            self.assertIn("test_similar_but_unknown", failed.stderr)
            target = workspace / "adapter.py"
            target.write_text(target.read_text(encoding="utf-8").replace(
                "ALIASES.get(name, name.lower())", "ALIASES.get(name, name)"), encoding="utf-8")
            corrected = self.run_fixture(workspace, "test_adapter.py", "test_contract.py")
            self.assertEqual(corrected.returncode, 0, corrected.stdout + corrected.stderr)
            self.assertIn("Ran 4 tests", corrected.stderr)
            self.assertEqual(ea.audit_tools(ROOT).verify_packet(packet, digest)
                             ["byte_integrity"], "pass")

    def test_continuation_fixture_preserves_completed_unit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="rdc-continuation-") as directory:
            parent = Path(directory).resolve()
            packet, digest = self.prepare(parent, "RDC-06-resume-valid")
            workspace = parent / "work"
            shutil.copytree(packet / "inputs", workspace)
            ready = self.run_fixture(workspace, "test_adapter.AdapterTests.test_exact_alias")
            self.assertEqual(ready.returncode, 0, ready.stdout + ready.stderr)
            incomplete = self.run_fixture(workspace)
            self.assertEqual(incomplete.returncode, 1, incomplete.stdout + incomplete.stderr)
            target = workspace / "adapter.py"
            target.write_text(target.read_text(encoding="utf-8").replace(
                "ALIASES.get(name, name.lower())", "ALIASES.get(name, name)"), encoding="utf-8")
            completed = self.run_fixture(workspace)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            for name in ("research.md", "plan.md", "test_adapter.py"):
                self.assertEqual((workspace / name).read_bytes(),
                                 (packet / "inputs" / name).read_bytes())
            self.assertEqual(ea.audit_tools(ROOT).verify_packet(packet, digest)
                             ["byte_integrity"], "pass")

    def test_method_drift_is_detected_without_rejecting_untouched_control(self) -> None:
        with tempfile.TemporaryDirectory(prefix="rdc-drift-") as directory:
            parent = Path(directory).resolve()
            changed, digest = self.prepare(parent, skill_roots=(SKILL,))
            control, control_digest = self.prepare(parent, skill_roots=(SKILL,))
            before = hashes(SKILL)
            (changed / "skill" / NAME / "SKILL.md").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Packet drift"):
                ea.audit_tools(ROOT).verify_packet(changed, digest)
            self.assertEqual(ea.audit_tools(ROOT).verify_packet(control, control_digest)
                             ["byte_integrity"], "pass")
            self.assertEqual(hashes(SKILL), before)


if __name__ == "__main__":
    unittest.main()
