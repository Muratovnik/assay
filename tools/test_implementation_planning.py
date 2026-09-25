"""Planning corpus packets and consumer routes; no model grading.

Pair and schema validation belong to the evaluation-data gate, refusal cases of
the shared packet utility to test_validation.py and native links to the
compatibility fixture.
"""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import assay as aa
import eval_assets as ea

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/implementation-planning"
EVALS = SKILL / "evals"
NAME = "implementation-planning"


class PlanningCorpusTests(unittest.TestCase):
    def test_registered_in_existing_checker(self) -> None:
        # The gate checks only registered corpora; dropping the name would pass silently.
        self.assertEqual(ea.PAIRED_SKILLS.count(NAME), 1)


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
            # The runtime package is the entrypoint, the Codex adapter and references.
            expected = {f"skill/{NAME}/SKILL.md", f"skill/{NAME}/agents/openai.yaml"}
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


class PlanningConsumerTests(unittest.TestCase):
    def test_consumers_link_into_the_method(self) -> None:
        # Consumers route to the method by link; which file they target may change.
        for name in ("code-maintenance", "operations-ui-delivery", "independent-audit"):
            with self.subTest(consumer=name):
                path = ROOT / "skills" / name / "SKILL.md"
                targets = aa.MARKDOWN_LINK.findall(path.read_text(encoding="utf-8"))
                resolved = [(path.parent / target.split("#", 1)[0]).resolve()
                            for target in targets if not target.startswith(("http", "#"))]
                self.assertTrue(any(SKILL.resolve() in target.parents and target.is_file()
                                    for target in resolved))


if __name__ == "__main__":
    unittest.main()
