"""Integrity of transfer fixtures; no model execution or behavioral pass claims."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

from eval_assets import check_pair, collections, load, metadata_path

ROOT = Path(__file__).resolve().parents[1]
SUPPLEMENTS = (
    ("ui-delivery", "anti-slop"),
    ("code-change", "comment-editing"),
    ("text-writing", "claim-preservation"),
)


class AntiSlopAssetsTest(unittest.TestCase):
    def test_inputs_rubrics_and_metadata_use_the_existing_contract(self) -> None:
        # UI retains its legacy main corpus. Validate this inline supplement with
        # the existing checker rather than changing that corpus or adding a runner.
        for skill, stem in SUPPLEMENTS:
            with self.subTest(skill=skill):
                directory = ROOT / "skills" / skill / "evals"
                cases = directory / f"{stem}-cases.json"
                self.assertTrue(metadata_path(cases).is_file())
                check_pair(cases, directory / f"{stem}-rubric.json", skill, tracked=True)

    def test_every_decision_case_keeps_its_paired_control(self) -> None:
        for skill, stem in SUPPLEMENTS:
            with self.subTest(skill=skill):
                directory = ROOT / "skills" / skill / "evals"
                cases_path = directory / f"{stem}-cases.json"
                cases = load(cases_path)
                rubric = load(directory / f"{stem}-rubric.json")
                metadata = load(metadata_path(cases_path))
                groups = {record["id"]: record["group"] for record in metadata["cases"]}
                paired_ids: list[str] = []
                self.assertTrue(rubric["pairs"])
                for pair in rubric["pairs"]:
                    self.assertEqual(len(pair["ids"]), 2)
                    self.assertEqual(len(set(pair["ids"])), 2)
                    self.assertTrue(pair["distinction"].strip())
                    self.assertEqual(len({groups[ident] for ident in pair["ids"]}), 1)
                    paired_ids.extend(pair["ids"])
                self.assertEqual(Counter(paired_ids), Counter(record["id"] for record in cases["cases"]))

    def test_oracles_are_nonempty_and_the_protocol_is_available(self) -> None:
        protocol = ROOT / "skills/skill-evaluation/evals/anti-slop-transfer.md"
        self.assertTrue(protocol.is_file())
        for skill, stem in SUPPLEMENTS:
            with self.subTest(skill=skill):
                rubric = load(ROOT / "skills" / skill / "evals" / f"{stem}-rubric.json")
                for collection, records in collections(rubric).items():
                    for record in records:
                        if collection == "cases":
                            self.assertIsInstance(record["assess"], list)
                            self.assertTrue(record["assess"])
                            for criterion in record["assess"]:
                                self.assertIsInstance(criterion, str)
                                self.assertTrue(criterion.strip())
                        else:
                            self.assertIsInstance(record["expected_route"], str)
                            self.assertTrue(record["expected_route"].strip())


if __name__ == "__main__":
    unittest.main()
