"""Exercise evaluation assets and real packet boundaries, not model behavior."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools import eval_assets as ea


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "skills/skill-evaluation/evals"


def write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document) + "\n", encoding="utf-8")


def inputs(name: str = "skill-evaluation") -> dict:
    return {"schema_version": 1, "skill_name": name,
            "cases": [{"id": "one", "prompt": "Inspect the supplied record.",
                       "files": {"record.txt": "Task evidence, not a grading key."}}]}


def sidecar(source: dict) -> dict:
    return {"schema_version": 1, "skill_name": source["skill_name"], **{
        key: [{"id": row["id"], "group": row["id"], "purpose": "routine",
               "source": "Synthetic test fixture", "rationale": "Boundary test",
               "split": "working", "exposure": "public"} for row in records]
        for key, records in ea.collections(source).items()}}


def rubric(source: dict) -> dict:
    return {"schema_version": 1, "skill_name": source["skill_name"], **{
        key: [{"id": row["id"], "required": ["Use the evidence."],
               "reject": ["Invent a run."]} for row in records]
        for key, records in ea.collections(source).items()}}


class MetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name).resolve()
        self.source = inputs()
        self.cases = self.directory / "cases.json"
        self.rubric = self.directory / "rubric.json"
        self.metadata = self.directory / "case-metadata.json"
        write_json(self.cases, self.source)
        write_json(self.rubric, rubric(self.source))

    def check_metadata(self, document: dict) -> None:
        write_json(self.metadata, document)
        ea.check_pair(self.cases, self.rubric, "skill-evaluation")

    def test_existing_pair_without_metadata_remains_supported(self) -> None:
        ea.check_pair(self.cases, self.rubric, "skill-evaluation")
        self.check_metadata(sidecar(self.source))

    def test_auxiliary_pair_uses_its_own_metadata(self) -> None:
        cases = self.directory / "trigger-cases.json"
        criteria = self.directory / "trigger-rubric.json"
        write_json(cases, self.source)
        write_json(criteria, rubric(self.source))
        meta = self.directory / "trigger-case-metadata.json"
        write_json(meta, sidecar(self.source))
        ea.check_pair(cases, criteria, "skill-evaluation")
        meta.write_text("{", encoding="utf-8")
        with self.assertRaises(ValueError):
            ea.check_pair(cases, criteria, "skill-evaluation")

    def test_metadata_identity_membership_and_classification_fail_closed(self) -> None:
        valid = sidecar(self.source)
        mutations = [
            lambda d: d.update(schema_version=True),
            lambda d: d.update(schema_version=1.0),
            lambda d: d.update(skill_name="other"),
            lambda d: d.update(unknown=[]),
            lambda d: d.update(cases=[]),
            lambda d: d.update(discovery_cases=copy.deepcopy(d["cases"])),
            lambda d: d["cases"].append(copy.deepcopy(d["cases"][0])),
            lambda d: d["cases"][0].update(id="missing"),
            lambda d: d["cases"][0].pop("rationale"),
            lambda d: d["cases"][0].update(answer="pass"),
            lambda d: d["cases"][0].update(group=" "),
            lambda d: d["cases"][0].update(group=" padded"),
            lambda d: d["cases"][0].update(source=None),
            lambda d: d["cases"][0].update(purpose="difficult"),
            lambda d: d["cases"][0].update(split="test"),
            lambda d: d["cases"][0].update(exposure="secret"),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(mutation=i):
                document = copy.deepcopy(valid)
                mutate(document)
                with self.assertRaises(ValueError):
                    self.check_metadata(document)

    def test_final_requires_sealed_declaration_not_proof_of_secrecy(self) -> None:
        for exposure in ("public", "development"):
            with self.subTest(exposure=exposure):
                document = sidecar(self.source)
                document["cases"][0].update(split="final", exposure=exposure)
                with self.assertRaisesRegex(ValueError, "sealed"):
                    self.check_metadata(document)
        document["cases"][0]["exposure"] = "sealed"
        self.check_metadata(document)

    def test_group_cannot_cross_splits_even_across_collections(self) -> None:
        self.source["discovery_cases"] = [{"id": "two", "prompt": "Inspect another record."}]
        write_json(self.cases, self.source)
        write_json(self.rubric, rubric(self.source))
        document = sidecar(self.source)
        document["discovery_cases"][0].update(group="one", split="selection")
        with self.assertRaisesRegex(ValueError, "group crosses"):
            self.check_metadata(document)
        document["discovery_cases"][0]["split"] = "working"
        self.check_metadata(document)

    def test_duplicate_json_keys_and_nonfinite_constants_are_rejected(self) -> None:
        for text in ('{"schema_version":1,"schema_version":1}', '{"value":NaN}'):
            with self.subTest(text=text):
                self.metadata.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    ea.check_pair(self.cases, self.rubric, "skill-evaluation")

    def test_evaluator_fields_cannot_move_into_executor_case(self) -> None:
        for field in ("group", "purpose", "source", "rationale", "split", "exposure", "required"):
            with self.subTest(field=field):
                source = copy.deepcopy(self.source)
                source["cases"][0][field] = "evaluator only"
                write_json(self.cases, source)
                with self.assertRaisesRegex(ValueError, "unsupported fields"):
                    ea.check_pair(self.cases, self.rubric, "skill-evaluation")


class CorpusAndPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name).resolve()
        self.outputs = self.directory / "packets"
        self.outputs.mkdir()

    def test_shipped_corpus_has_criteria_and_public_working_metadata(self) -> None:
        ea.check_pair(CORPUS / "cases.json", CORPUS / "rubric.json", "skill-evaluation")
        source = ea.load(CORPUS / "cases.json")
        criteria = ea.load(CORPUS / "rubric.json")
        metadata = ea.load(CORPUS / "case-metadata.json")
        self.assertIn("skill-evaluation", ea.PAIRED_SKILLS)
        self.assertEqual({"cases", "discovery_cases"}, set(ea.collections(source)))
        purposes = set()
        for key, rows in ea.collections(source).items():
            self.assertTrue(rows)
            for row in criteria[key]:
                for field in ("required", "reject"):
                    self.assertIsInstance(row[field], list)
                    self.assertTrue(row[field])
                    self.assertTrue(all(isinstance(x, str) and x.strip() for x in row[field]))
            for row in metadata[key]:
                self.assertEqual("working", row["split"])
                self.assertEqual("public", row["exposure"])
                purposes.add(row["purpose"])
        self.assertEqual({"routine", "regression", "challenge", "should-not-fire"}, purposes)

    def test_every_case_prepares_only_exact_inputs_with_verifiable_bytes(self) -> None:
        source = ea.load(CORPUS / "cases.json")
        verifier = ea.audit_tools()
        for collection, records in ea.collections(source).items():
            for case in records:
                with self.subTest(collection=collection, case=case["id"]):
                    packet, digest = ea.prepare(cases_path=CORPUS / "cases.json",
                        case_id=case["id"], collection=collection, output_parent=self.outputs)
                    expected = {"prompt.txt", "manifest.json"}
                    expected.update("inputs/" + name for name in case.get("files", {}))
                    if "context" in case:
                        expected.add("context.txt")
                    observed = {p.relative_to(packet).as_posix() for p in packet.rglob("*") if p.is_file()}
                    self.assertEqual(expected, observed)
                    self.assertEqual(case["prompt"] + "\n", (packet / "prompt.txt").read_text(encoding="utf-8"))
                    if "context" in case:
                        self.assertEqual(case["context"].encode("utf-8") + b"\n",
                                         (packet / "context.txt").read_bytes())
                    for name, text in case.get("files", {}).items():
                        self.assertEqual(text.encode("utf-8"), (packet / "inputs" / name).read_bytes())
                    self.assertEqual("pass", verifier.verify_packet(packet, digest)["byte_integrity"])

    def test_context_bytes_are_preserved(self) -> None:
        cases = self.directory / "source" / "evals" / "cases.json"
        verifier = ea.audit_tools()
        contexts = ("Первая строка — café\n\n\t第二行  ", "Уже с переводом строки\n",
                    "CRLF\r\nСтрока  \r\n", "")
        for context in contexts:
            with self.subTest(context=context):
                source = inputs()
                source["cases"][0]["context"] = context
                write_json(cases, source)
                packet, digest = ea.prepare(cases_path=cases, case_id="one",
                                            output_parent=self.outputs)
                context_path = packet / "context.txt"
                self.assertTrue(context_path.is_file(), "Supplied context must be packaged")
                # The packet contract appends one LF; it does not normalize input text.
                self.assertEqual(context.encode("utf-8") + b"\n", context_path.read_bytes())
                self.assertIn("context.txt", ea.load(packet / "manifest.json")["files"])
                self.assertEqual("pass", verifier.verify_packet(packet, digest)["byte_integrity"])
                context_path.write_bytes(b"changed\n")
                with self.assertRaisesRegex(ValueError, "drift"):
                    verifier.verify_packet(packet, digest)

    def test_method_snapshot_excludes_keys_even_when_coordinator_files_are_invalid(self) -> None:
        method = self.directory / "skill-evaluation"
        ev = method / "evals"
        refs = method / "references"
        refs.mkdir(parents=True)
        ev.mkdir()
        (method / "SKILL.md").write_text("Method instruction.\n", encoding="utf-8")
        (refs / "procedure.md").write_text("Conditional method.\n", encoding="utf-8")
        write_json(ev / "cases.json", inputs())
        # Invalid coordinator JSON detects accidental reading as well as copying.
        (ev / "rubric.json").write_text("PRIVATE_RUBRIC{", encoding="utf-8")
        (ev / "case-metadata.json").write_text("PRIVATE_METADATA{", encoding="utf-8")
        (ev / "previous-answer.txt").write_text("PRIVATE_ANSWER", encoding="utf-8")
        packet, digest = ea.prepare(cases_path=ev / "cases.json", case_id="one",
                                    output_parent=self.outputs, skill_roots=(method,))
        expected = {"prompt.txt", "manifest.json", "inputs/record.txt",
                    "skill/skill-evaluation/SKILL.md", "skill/skill-evaluation/references/procedure.md"}
        self.assertEqual(expected, {p.relative_to(packet).as_posix() for p in packet.rglob("*") if p.is_file()})
        for p in packet.rglob("*"):
            if p.is_file():
                self.assertNotIn(b"PRIVATE_", p.read_bytes())
        ea.audit_tools().verify_packet(packet, digest)
        (packet / "inputs/record.txt").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "drift"):
            ea.audit_tools().verify_packet(packet, digest)

    def test_invalid_input_is_rejected_before_allocating_a_packet(self) -> None:
        cases = self.directory / "source" / "evals" / "cases.json"
        source = inputs()
        source["cases"][0]["split"] = "final"
        write_json(cases, source)
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            ea.prepare(cases_path=cases, case_id="one", output_parent=self.outputs)
        self.assertEqual([], list(self.outputs.iterdir()))

    def test_ui_case_prepares_without_exposing_trigger_labels(self) -> None:
        directory = ROOT / "skills/ui-delivery/evals"
        source = ea.load(directory / "cases.json")["cases"][0]
        packet, digest = ea.prepare(cases_path=directory / "cases.json",
            case_id=source["id"], output_parent=self.outputs)
        self.assertEqual(source["prompt"] + "\n", (packet / "prompt.txt").read_text(encoding="utf-8"))
        self.assertEqual(source["context"] + "\n", (packet / "context.txt").read_text(encoding="utf-8"))
        ea.audit_tools().verify_packet(packet, digest)
        before = set(self.outputs.iterdir())
        labelled = ea.load(directory / "trigger-cases.json")["cases"][0]
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            ea.prepare(cases_path=directory / "trigger-cases.json",
                case_id=labelled["id"], output_parent=self.outputs)
        self.assertEqual(before, set(self.outputs.iterdir()))


class RepositoryGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        for name in ea.PAIRED_SKILLS:
            directory = self.root / "skills" / name / "evals"
            source = inputs(name)
            write_json(directory / "cases.json", source)
            write_json(directory / "rubric.json", rubric(source))
        self.ev = self.root / "skills/skill-evaluation/evals"
        (self.ev / "research-and-transfer.md").write_text("Manual specifications.\n", encoding="utf-8")
        audit = self.root / "skills/independent-audit/evals"
        audit.mkdir(parents=True)
        shutil.copyfile(ROOT / "skills/independent-audit/evals/prepare_case.py", audit / "prepare_case.py")
        (audit / "files/1").mkdir(parents=True)
        (audit / "files/1/brief.md").write_text("Synthetic audit input.\n", encoding="utf-8")
        write_json(audit / "evals.json", {"skill_name": "independent-audit", "evals": [
            {"id": 1, "prompt": "Inspect the brief.", "expected_output": "A scoped result.",
             "files": ["files/1/brief.md"], "assertions": ["Do not invent evidence."]}]})
        # UI decisions use the shared input schema; legacy trigger labels do not.
        ui = self.root / "skills/ui-delivery/evals"
        write_json(ui / "cases.json", inputs("ui-delivery"))
        write_json(ui / "rubric.json", rubric(inputs("ui-delivery")))
        for name, path in (("ui-delivery", ui / "trigger-cases.json"),
                           ("independent-audit", audit / "trigger-evals.json")):
            shutil.copyfile(ROOT / "skills" / name / "evals" / path.name, path)

    def test_gate_checks_ui_case_and_rubric_in_both_directions(self) -> None:
        directory = self.root / "skills/ui-delivery/evals"
        for field in ("prompt", "rubric_id"):
            with self.subTest(field=field):
                source = inputs("ui-delivery")
                criteria = rubric(source)
                if field == "prompt":
                    source["cases"][0]["prompt"] = ""
                else:
                    criteria["cases"][0]["id"] = "missing"
                write_json(directory / "cases.json", source)
                write_json(directory / "rubric.json", criteria)
                with self.assertRaises(ValueError):
                    ea.check(self.root)
        write_json(directory / "cases.json", inputs("ui-delivery"))
        write_json(directory / "rubric.json", rubric(inputs("ui-delivery")))
        self.assertIn("ui-delivery", ea.check(self.root))

    def test_gate_validates_labelled_trigger_formats_without_scoring_them(self) -> None:
        for name, filename in (("ui-delivery", "trigger-cases.json"),
                               ("independent-audit", "trigger-evals.json")):
            path = self.root / "skills" / name / "evals" / filename
            valid = ea.load(path)
            for field, value in (("should_trigger", "false"), ("should_trigger", 1),
                                 ("prompt", " ")):
                with self.subTest(skill=name, field=field, value=value):
                    invalid = copy.deepcopy(valid)
                    invalid["cases"][0][field] = value
                    write_json(path, invalid)
                    with self.assertRaises(ValueError):
                        ea.check(self.root)
            write_json(path, valid)
        ea.check(self.root)

    def test_gate_checks_new_skill_without_a_manual_only_override(self) -> None:
        report = ea.check(self.root)
        self.assertEqual("input/rubric structure checked, no model run", report["skill-evaluation"])
        (self.ev / "cases.json").unlink()
        with self.assertRaises(OSError):
            ea.check(self.root)

    def test_gate_detects_groups_crossing_auxiliary_corpora(self) -> None:
        source = inputs()
        write_json(self.ev / "case-metadata.json", sidecar(source))
        write_json(self.ev / "extra-cases.json", source)
        write_json(self.ev / "extra-rubric.json", rubric(source))
        extra = sidecar(source)
        extra["cases"][0]["split"] = "selection"
        write_json(self.ev / "extra-case-metadata.json", extra)
        with self.assertRaisesRegex(ValueError, "group crosses"):
            ea.check(self.root)
        extra["cases"][0]["group"] = "different-incident"
        write_json(self.ev / "extra-case-metadata.json", extra)
        ea.check(self.root)

    def test_gate_rejects_orphan_sidecars(self) -> None:
        write_json(self.ev / "forgotten-case-metadata.json", sidecar(inputs()))
        with self.assertRaisesRegex(ValueError, "orphan"):
            ea.check(self.root)

    def test_gate_accepts_only_public_metadata_in_tracked_corpora(self) -> None:
        # A tracked corpus is published: no label makes it sealed or final.
        for name in ("skill-evaluation", "test-audit"):
            directory = self.root / "skills" / name / "evals"
            for split, exposure in (("final", "sealed"), ("working", "development")):
                with self.subTest(skill=name, split=split, exposure=exposure):
                    document = sidecar(inputs(name))
                    document["cases"][0].update(split=split, exposure=exposure)
                    write_json(directory / "case-metadata.json", document)
                    with self.assertRaisesRegex(ValueError, f"{name}: .*must be public"):
                        ea.check(self.root)
            write_json(directory / "case-metadata.json", sidecar(inputs(name)))
        ea.check(self.root)


if __name__ == "__main__":
    unittest.main()
