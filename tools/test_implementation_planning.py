"""Planning corpus, packet and native integration contracts; no model grading."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

import eval_assets as ea

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/implementation-planning"
EVALS = SKILL / "evals"
NAME = "implementation-planning"


def write_json(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, ensure_ascii=False) + "\n", encoding="utf-8")


class PlanningCorpusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = ea.load(EVALS / "cases.json")
        self.rubric = ea.load(EVALS / "rubric.json")

    def check_mutation(self, cases: dict, rubric: dict) -> None:
        with tempfile.TemporaryDirectory(prefix="planning-data-") as directory:
            root = Path(directory)
            write_json(root / "cases.json", cases)
            write_json(root / "rubric.json", rubric)
            ea.check_pair(root / "cases.json", root / "rubric.json", NAME)

    def test_registered_in_existing_checker(self) -> None:
        self.assertIn(NAME, ea.PAIRED_SKILLS)
        self.assertEqual(ea.PAIRED_SKILLS.count(NAME), 1)

    def test_valid_pair(self) -> None:
        self.check_mutation(self.cases, self.rubric)

    def test_each_case_is_input_only(self) -> None:
        for collection, cases in ea.collections(self.cases).items():
            for case in cases:
                with self.subTest(collection=collection, case=case["id"]):
                    self.assertLessEqual(set(case), ea.INPUT_KEYS)
                    self.assertIs(ea.input_case(case), case)

    def test_discovery_and_neighbor_controls_are_distinct_inputs(self) -> None:
        primary = {case["id"]: case for case in self.cases["cases"]}
        for first, second in (("full-migration", "pilot-only"),
                              ("review-missing-acceptance", "review-valid-control"),
                              ("async-replan", "unapproved-drift")):
            with self.subTest(first=first, second=second):
                self.assertNotEqual(primary[first]["prompt"], primary[second]["prompt"])
        discovery = {case["id"] for case in self.cases["discovery_cases"]}
        self.assertTrue({"idea-discussion", "explicit-small-plan", "obvious-edit",
                         "research-only", "implementation-already-authorized",
                         "plan-audit"} <= discovery)

    def test_mismatched_rubric_id_rejected(self) -> None:
        self.rubric["cases"][0]["id"] = "unmatched-case"
        with self.assertRaises(ValueError):
            self.check_mutation(self.cases, self.rubric)

    def test_wrong_skill_identity_rejected(self) -> None:
        self.cases["skill_name"] = "different-skill"
        with self.assertRaises(ValueError):
            self.check_mutation(self.cases, self.rubric)

    def test_missing_discovery_rubric_rejected(self) -> None:
        del self.rubric["discovery_cases"]
        with self.assertRaises(ValueError):
            self.check_mutation(self.cases, self.rubric)

    def test_duplicate_ids_rejected(self) -> None:
        self.cases["cases"].append(copy.deepcopy(self.cases["cases"][0]))
        with self.assertRaises(ValueError):
            self.check_mutation(self.cases, self.rubric)

    def test_grading_field_in_executor_input_rejected(self) -> None:
        self.cases["cases"][0]["expected_output"] = "grading sentinel"
        with self.assertRaises(ValueError):
            self.check_mutation(self.cases, self.rubric)

    def test_unsafe_inline_path_rejected(self) -> None:
        self.cases["cases"][0]["files"] = {"../rubric.json": "not an input"}
        with self.assertRaises(ValueError):
            self.check_mutation(self.cases, self.rubric)


class PlanningPacketTests(unittest.TestCase):
    def prepare(self, parent: Path, case: str = "bounded-form", **kwargs):
        return ea.prepare(cases_path=EVALS / "cases.json", case_id=case,
                          output_parent=parent, root=ROOT, **kwargs)

    def test_all_cases_prepare_with_only_named_inputs(self) -> None:
        document = ea.load(EVALS / "cases.json")
        with tempfile.TemporaryDirectory(prefix="planning-packets-") as directory:
            for collection, cases in ea.collections(document).items():
                for case in cases:
                    with self.subTest(collection=collection, case=case["id"]):
                        packet, digest = self.prepare(Path(directory), case["id"],
                                                      collection=collection)
                        expected = {"prompt.txt", "manifest.json"}
                        if "context" in case:
                            expected.add("context.txt")
                        expected.update("inputs/" + name for name in case.get("files", {}))
                        actual = {p.relative_to(packet).as_posix()
                                  for p in packet.rglob("*") if p.is_file()}
                        self.assertEqual(actual, expected)
                        self.assertEqual((packet / "prompt.txt").read_text(encoding="utf-8"),
                                         case["prompt"] + "\n")
                        for name, text in case.get("files", {}).items():
                            self.assertEqual((packet / "inputs" / name).read_bytes(),
                                             text.encode("utf-8"))
                        result = ea.audit_tools(ROOT).verify_packet(packet, digest)
                        self.assertEqual(result["byte_integrity"], "pass")

    def test_method_snapshot_excludes_evaluation_and_other_skills(self) -> None:
        before = {p.relative_to(SKILL).as_posix(): p.read_bytes()
                  for p in SKILL.rglob("*") if p.is_file()}
        with tempfile.TemporaryDirectory(prefix="planning-method-") as directory:
            packet, digest = self.prepare(Path(directory), skill_roots=(SKILL,))
            runtime = {p.relative_to(packet).as_posix() for p in packet.rglob("*")
                       if p.is_file() and p.relative_to(packet).parts[0] == "skill"}
            expected = {f"skill/{NAME}/SKILL.md"}
            expected.update(f"skill/{NAME}/" + p.relative_to(SKILL).as_posix()
                            for p in (SKILL / "references").rglob("*") if p.is_file())
            self.assertEqual(runtime, expected)
            self.assertFalse(any("evals" in Path(name).parts for name in runtime))
            ea.audit_tools(ROOT).verify_packet(packet, digest)
        self.assertEqual(before, {p.relative_to(SKILL).as_posix(): p.read_bytes()
                                  for p in SKILL.rglob("*") if p.is_file()})

    def test_with_and_without_method_preserve_same_task_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="planning-pair-") as directory:
            plain, _ = self.prepare(Path(directory))
            treated, _ = self.prepare(Path(directory), skill_roots=(SKILL,))
            for path in plain.rglob("*"):
                if path.is_file() and path.name != "manifest.json":
                    self.assertEqual(path.read_bytes(),
                                     (treated / path.relative_to(plain)).read_bytes())

    def test_postflight_detects_changed_prompt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="planning-drift-") as directory:
            packet, digest = self.prepare(Path(directory))
            (packet / "prompt.txt").write_text("changed\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                ea.audit_tools(ROOT).verify_packet(packet, digest)

    def test_unknown_case_does_not_allocate_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="planning-unknown-") as directory:
            parent = Path(directory)
            with self.assertRaises(ValueError):
                self.prepare(parent, "not-a-case")
            self.assertEqual(list(parent.iterdir()), [])

    def test_unsupported_skill_does_not_allocate_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="planning-unsupported-") as directory:
            parent = Path(directory)
            cases = ea.load(EVALS / "cases.json")
            cases["skill_name"] = "not-registered"
            source = parent / "cases.json"
            write_json(source, cases)
            with self.assertRaises(ValueError):
                ea.prepare(cases_path=source, case_id="bounded-form",
                           output_parent=parent, root=ROOT)
            self.assertEqual(set(parent.iterdir()), {source})

    def test_duplicate_methods_do_not_allocate_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="planning-duplicates-") as directory:
            parent = Path(directory)
            with self.assertRaises(ValueError):
                self.prepare(parent, skill_roots=(SKILL, SKILL))
            self.assertEqual(list(parent.iterdir()), [])

    def test_source_package_cannot_receive_packets(self) -> None:
        with self.assertRaises(ValueError):
            self.prepare(EVALS)


class PlanningIntegrationTests(unittest.TestCase):
    def test_catalog_and_independent_expectations_include_native_links(self) -> None:
        import assay as aa
        import compatibility_fixture as fixture
        catalog = aa.load_catalog(ROOT)
        asset = next(item for item in catalog.assets if item.id == f"skill/{NAME}")
        self.assertIn(asset.id, fixture.EXPECTED_ASSETS)
        self.assertEqual(asset.activation, "automatic")
        with tempfile.TemporaryDirectory(prefix="planning-native-") as directory:
            home = Path(directory)
            entries = [entry for entry in aa.native_plan(ROOT, home)
                       if entry.asset_id == asset.id]
            self.assertEqual(len(entries), 2)
            by_client = {entry.client: entry for entry in entries}
            self.assertEqual(by_client["codex"].source, SKILL)
            self.assertEqual(by_client["codex"].target, home / ".agents/skills" / NAME)
            self.assertEqual(by_client["claude"].source, home / ".agents/skills" / NAME)
            self.assertEqual(by_client["claude"].target, home / ".claude/skills" / NAME)
            self.assertTrue(all(entry.mode == "link" for entry in entries))

    def test_three_consumers_have_resolving_links(self) -> None:
        import assay as aa
        consumers = {
            "code-maintenance": SKILL / "SKILL.md",
            "operations-ui-delivery": SKILL / "SKILL.md",
            "independent-audit": SKILL / "references/review-and-replan.md",
        }
        for name, expected in consumers.items():
            with self.subTest(consumer=name):
                path = ROOT / "skills" / name / "SKILL.md"
                targets = aa.MARKDOWN_LINK.findall(path.read_text(encoding="utf-8"))
                resolved = {(path.parent / target.split("#", 1)[0]).resolve()
                            for target in targets if not target.startswith(("http", "#"))}
                self.assertIn(expected.resolve(), resolved)
                self.assertTrue(expected.is_file())

    def test_runtime_reference_links_resolve(self) -> None:
        import assay as aa
        for path in [SKILL / "SKILL.md", *(SKILL / "references").glob("*.md")]:
            with self.subTest(path=path.name):
                self.assertEqual(aa.markdown_problems(path, ROOT), [])


if __name__ == "__main__":
    unittest.main()
