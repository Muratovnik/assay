"""Architecture packaging and packet integration, not model-quality scores."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import tomllib
import unittest

from tools import eval_assets as ea

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/software-architecture"
CASES = SKILL / "evals/cases.json"
RUBRIC = SKILL / "evals/rubric.json"


def hashes(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}


class ArchitectureCorpusTests(unittest.TestCase):
    def test_catalog_registers_one_shared_native_skill(self) -> None:
        catalog = tomllib.loads((ROOT / "catalog.toml").read_text(encoding="utf-8"))
        matching = [a for a in catalog["assets"] if a["id"] == "skill/software-architecture"]
        self.assertEqual(len(matching), 1)
        asset = matching[0]
        self.assertEqual(asset["path"], "skills/software-architecture")
        self.assertEqual(asset["activation"], "automatic")
        self.assertEqual(asset["kind"], "skill")
        self.assertEqual(asset["license"], "MIT")
        self.assertEqual(asset["projections"], [
            {"client": "codex", "root": "agents", "path": "skills/software-architecture", "mode": "link"},
            {"client": "claude", "root": "claude", "path": "skills/software-architecture", "mode": "link"},
        ])

    def test_input_and_rubric_pairs_use_existing_protocol(self) -> None:
        self.assertIn("software-architecture", ea.PAIRED_SKILLS)
        ea.check_pair(CASES, RUBRIC, "software-architecture")
        cases, rubric = ea.load(CASES), ea.load(RUBRIC)
        self.assertEqual(set(cases), {"schema_version", "skill_name", "cases", "discovery_cases"})
        ids = {case["id"] for case in cases["cases"]}
        self.assertTrue({"ARC-01-plan", "ARC-01-implement", "ARC-03-invariant", "ARC-03-separate",
                         "ARC-04-lifecycle", "ARC-04-expression", "ARC-12-layout"} <= ids)
        self.assertIn("DISC-plan", {case["id"] for case in cases["discovery_cases"]})
        for record in rubric["cases"]:
            for key in ("must", "must_not"):
                self.assertIsInstance(record[key], list)
                self.assertTrue(record[key])
                self.assertTrue(all(isinstance(item, str) and item.strip() for item in record[key]))
        for record in rubric["discovery_cases"]:
            self.assertTrue(record["expected_methods"])
            self.assertTrue(record["avoid"])

    def test_grading_leak_rejected_with_valid_control(self) -> None:
        valid = copy.deepcopy(ea.load(CASES)["cases"][0])
        self.assertEqual(ea.input_case(valid), valid)
        leaked = valid | {"expected_output": "coordinator-only answer"}
        with self.assertRaisesRegex(ValueError, "grading data"):
            ea.input_case(leaked)
        self.assertNotIn("expected_output", valid)

    def test_new_runtime_references_and_consumer_routes_resolve(self) -> None:
        # Inspect only the new method and the integration edges owned by this change.
        # The existing audit snapshot suite checks its complete selected criteria set.
        for path in [SKILL / "SKILL.md", *(SKILL / "references").glob("*.md")]:
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if target.startswith(("https://", "http://", "#")):
                    continue
                linked = (path.parent / target.split("#", 1)[0]).resolve()
                linked.relative_to(ROOT.resolve())
                self.assertTrue(linked.is_file(), f"Missing runtime target: {path.name}: {target}")
                self.assertNotIn("evals", linked.relative_to(ROOT).parts)
        for relative in ("skills/code-change/SKILL.md",
                         "skills/implementation-planning/SKILL.md",
                         "skills/independent-audit/references/architecture-and-migration.md"):
            path = ROOT / relative
            targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8"))
            resolved = {(path.parent / item.split("#", 1)[0]).resolve()
                        for item in targets if "software-architecture" in item}
            self.assertIn((SKILL / "SKILL.md").resolve(), resolved, relative)


class ArchitecturePacketTests(unittest.TestCase):
    def test_direct_and_no_method_packets_keep_identical_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="assay-architecture-") as directory:
            parent = Path(directory).resolve()
            plain, plain_digest = ea.prepare(cases_path=CASES, case_id="ARC-07-exports",
                                             output_parent=parent, root=ROOT)
            enhanced, enhanced_digest = ea.prepare(cases_path=CASES, case_id="ARC-07-exports",
                                                   output_parent=parent, skill_roots=(SKILL,), root=ROOT)
            self.assertEqual(hashes(plain / "inputs"), hashes(enhanced / "inputs"))
            for name in ("prompt.txt", "context.txt"):
                self.assertEqual((plain / name).read_bytes(), (enhanced / name).read_bytes())
            self.assertFalse((plain / "skill").exists())
            self.assertTrue((enhanced / "skill/software-architecture/SKILL.md").is_file())
            for packet, digest in ((plain, plain_digest), (enhanced, enhanced_digest)):
                self.assertEqual(ea.audit_tools(ROOT).verify_packet(packet, digest)["byte_integrity"], "pass")

    def test_both_consumers_receive_explicit_criteria_without_evals(self) -> None:
        with tempfile.TemporaryDirectory(prefix="assay-architecture-") as directory:
            parent = Path(directory).resolve()
            for consumer, case_id in (("code-change", "ARC-01-implement"),
                                      ("independent-audit", "ARC-12-layout")):
                with self.subTest(consumer=consumer):
                    roots = (SKILL, ROOT / "skills" / consumer)
                    before = [hashes(root) for root in roots]
                    packet, digest = ea.prepare(cases_path=CASES, case_id=case_id,
                                                output_parent=parent, skill_roots=roots, root=ROOT)
                    self.assertEqual({p.name for p in (packet / "skill").iterdir()},
                                     {"software-architecture", consumer})
                    for root in roots:
                        runtime = [root / "SKILL.md", *(root / "references").rglob("*")]
                        runtime += list((root / "agents").glob("openai.yaml"))
                        expected = {p.relative_to(root).as_posix() for p in runtime if p.is_file()}
                        frozen = packet / "skill" / root.name
                        self.assertEqual(set(hashes(frozen)), expected)
                        for relative in expected:
                            self.assertEqual((root / relative).read_bytes(), (frozen / relative).read_bytes())
                    self.assertFalse(any("evals" in p.relative_to(packet).parts for p in packet.rglob("*")))
                    self.assertEqual([hashes(root) for root in roots], before)
                    self.assertEqual(ea.audit_tools(ROOT).verify_packet(packet, digest)["byte_integrity"], "pass")

    def test_modified_method_rejected_while_valid_packet_survives(self) -> None:
        with tempfile.TemporaryDirectory(prefix="assay-architecture-") as directory:
            parent = Path(directory).resolve()
            packet, digest = ea.prepare(cases_path=CASES, case_id="ARC-04-lifecycle",
                                        output_parent=parent, skill_roots=(SKILL,), root=ROOT)
            control, control_digest = ea.prepare(cases_path=CASES, case_id="ARC-04-lifecycle",
                                                 output_parent=parent, skill_roots=(SKILL,), root=ROOT)
            before = hashes(SKILL)
            (packet / "skill/software-architecture/SKILL.md").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Packet drift"):
                ea.audit_tools(ROOT).verify_packet(packet, digest)
            self.assertEqual(ea.audit_tools(ROOT).verify_packet(control, control_digest)["byte_integrity"], "pass")
            self.assertEqual(hashes(SKILL), before)

    def test_discovery_packet_does_not_expose_expected_route(self) -> None:
        with tempfile.TemporaryDirectory(prefix="assay-architecture-") as directory:
            packet, digest = ea.prepare(cases_path=CASES, case_id="DISC-audit",
                                        collection="discovery_cases", output_parent=Path(directory).resolve(), root=ROOT)
            self.assertEqual(set(hashes(packet)), {"prompt.txt", "context.txt", "manifest.json"})
            manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(set(manifest["files"]), {"prompt.txt", "context.txt"})
            self.assertEqual(ea.audit_tools(ROOT).verify_packet(packet, digest)["byte_integrity"], "pass")


if __name__ == "__main__":
    unittest.main()
