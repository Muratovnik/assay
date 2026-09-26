"""Research-driven-change registration and frozen inputs, not model grading.

Use the existing native-plan, case-pair and packet mechanisms. These checks
establish integration and input integrity, not workflow execution or savings.
"""
from __future__ import annotations

import copy
import hashlib
import re
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
