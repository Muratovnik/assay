"""Controls for denominator loss, invented certainty and evidence tampering."""

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import comparison_report as report


def requirements(*statuses):
    return [{"id": f"C-{i}", "status": status, "evidence": "fixture observation"}
            for i, status in enumerate(statuses, 1)]


def minimal_evidence():
    blobs = {}

    def retain(text):
        sha = report.digest(text.encode())
        blobs[sha] = text
        return sha

    source_sha = report.digest(b"fixed cases")
    source = retain("source")
    trials, runs, grades, events = [], [], [], []
    pair = ["method-a", "method-b"]
    for case, arms in (("C-M", ("00", "10", "01", "11")), ("C-C", ("00", "11"))):
        for arm in arms:
            run_id = f"R{len(trials) + 1:02d}"
            skills = [pair[i] for i, enabled in enumerate(arm) if enabled == "1"]
            files = {"inputs/source.txt": source}
            files.update({f"skill/{name}/SKILL.md": retain(name) for name in skills})
            manifest = retain(json.dumps({"case_id": case, "source_sha256": source_sha, "files": files}))
            trials.append({"run_id": run_id, "case_id": case, "block": "C", "arm": arm,
                           "skills": skills, "packet_files": files,
                           "packet_manifest_sha256": manifest, "launch_sha256": retain("launch")})
            runs.append({"run_id": run_id, "case_id": case, "status": "completed",
                         "output_files": {"answer.md": retain("answer"), "source.txt": source},
                         "source_files": {"source.txt": source}, "changed_source_files": [], "new_files": ["answer.md"]})
            grades.append({"run_id": run_id, "case_id": case, "arm": arm,
                           "requirements": requirements("met", "not_verified")})
            events.extend({"run_id": run_id, "event": event} for event in ("spawn_observed", "completion_observed"))
    plan = {"trials": trials, "input_digests": {"comparison-cases.json": source_sha},
            "blocks": [{"id": "C", "main_case": "C-M", "control_case": "C-C", "skills": pair}]}
    evidence = {"runs": runs, "blobs": blobs, "execution_events": events}
    grades = {"runs": grades}
    rubric = {"cases": [{"id": case, "requirements": requirements("met", "met")} for case in ("C-M", "C-C")]}
    return plan, evidence, grades, rubric


def add_receipt(data, *, suite_status="met"):
    evidence = data[1]
    run = evidence["runs"][0]
    checker = report.digest(b"constructed checker")
    evidence["blobs"][checker] = "constructed checker"
    receipt = {"run_id": run["run_id"], "case": run["case_id"], "checker_sha256": checker,
               "subject_inventory_sha256": report.digest(json.dumps(run["output_files"], sort_keys=True).encode()),
               "evaluator_preserved_subject_bytes": True,
               "criteria": requirements("met", "not_verified"),
               "evidence": {"submitted_suite_assessment": {"status": suite_status}}}
    text = json.dumps(receipt)
    sha = report.digest(text.encode())
    evidence["blobs"][sha] = text
    evidence["deterministic_receipts"] = {run["run_id"]: {"v2_blob_sha256": sha}}
    return receipt, sha


class ComparisonReportControls(unittest.TestCase):
    def test_unknown_is_an_interval_not_zero_or_success(self):
        value = report.outcome(requirements("met", "not_verified"))
        self.assertIsNone(value["requirement_fraction"])
        self.assertEqual([0.5, 1.0], value["requirement_fraction_interval"])
        self.assertEqual("not_verified", value["strict"])
        self.assertEqual([0, 1], value["strict_interval"])

    def test_refuted_guard_cannot_be_offset(self):
        value = report.outcome(requirements("met", "met", "refuted", "not_verified"))
        self.assertEqual("refuted", value["strict"])
        self.assertEqual([0, 0], value["strict_interval"])
        with self.assertRaises(ValueError):
            report.outcome([])

    def test_uncertain_baseline_preserves_both_contrast_bounds(self):
        arms = {"00": report.outcome(requirements("met", "not_verified")),
                "11": report.outcome(requirements("met", "met"))}
        value = report.linear_contrast(arms, {"11": 1, "00": -1})
        self.assertEqual({"value": None, "interval": [0.0, 0.5]}, value)

    def test_fully_observed_interaction_and_ceiling(self):
        arms = {arm: report.outcome(requirements(*statuses)) for arm, statuses in {
            "00": ("met", "refuted"), "10": ("met", "met"),
            "01": ("met", "met"), "11": ("met", "met")}.items()}
        self.assertEqual(-0.5, report.linear_contrast(arms, {"11": 1, "10": -1, "01": -1, "00": 1})["value"])

    def test_legitimate_retained_fixture_and_missing_allocations(self):
        data = minimal_evidence()
        report.verify(*data)
        changed = copy.deepcopy(data)
        changed[1]["runs"].clear()
        with self.assertRaises(ValueError):
            report.verify(*changed)

    def test_empty_campaign_and_lost_declared_task_are_rejected(self):
        with self.assertRaises(ValueError):
            report.summarize({"trials": [], "blocks": []},
                             {"runs": [], "blobs": {}, "execution_events": []},
                             {"runs": []}, {"cases": []})
        data = minimal_evidence()
        for owner, field in ((0, "trials"), (1, "runs"), (2, "runs")):
            data[owner][field] = [row for row in data[owner][field] if row["case_id"] != "C-C"]
        with self.assertRaises(ValueError):
            report.verify(*data)

    def test_duplicate_case_and_mismatched_method_condition_are_rejected(self):
        data = minimal_evidence()
        data[3]["cases"].append(copy.deepcopy(data[3]["cases"][0]))
        with self.assertRaises(ValueError):
            report.verify(*data)
        data = minimal_evidence()
        data[0]["trials"][0]["skills"] = ["method-a"]
        with self.assertRaises(ValueError):
            report.verify(*data)

    def test_contradictory_grade_and_capture_identities_are_rejected(self):
        for field, value in (("case_id", "C-C"), ("arm", "11")):
            data = minimal_evidence()
            data[2]["runs"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                report.verify(*data)
        data = minimal_evidence()
        data[1]["runs"][0]["changed_source_files"] = ["source.txt"]
        with self.assertRaises(ValueError):
            report.verify(*data)

    def test_malformed_grade_and_unknown_event_are_rejected(self):
        for value in ([], {}, None, 0):
            data = minimal_evidence()
            data[2]["runs"][0]["requirements"][0]["evidence"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                report.verify(*data)
        data = minimal_evidence()
        data[1]["execution_events"][0]["event"] = "invented"
        with self.assertRaises(ValueError):
            report.verify(*data)

    def test_malformed_input_digest_container_returns_controlled_failure(self):
        data = minimal_evidence()
        data[0]["input_digests"] = []
        output = io.StringIO()
        with patch.object(report, "read_json", side_effect=data), patch("sys.argv", ["comparison_report.py", "check"]), patch("sys.stdout", output):
            self.assertEqual(1, report.main())
        self.assertIn("comparison evidence: FAIL", output.getvalue())

    def test_duplicate_runs_and_criteria_are_rejected(self):
        for owner, field in [(1, "runs"), (2, "runs")]:
            data = minimal_evidence()
            data[owner][field].append(copy.deepcopy(data[owner][field][0]))
            with self.assertRaises(ValueError):
                report.verify(*data)
        data = minimal_evidence()
        data[2]["runs"][0]["requirements"].append(data[2]["runs"][0]["requirements"][0])
        with self.assertRaises(ValueError):
            report.verify(*data)

    def test_tampered_blob_and_missing_receipt_are_rejected(self):
        data = minimal_evidence()
        sha = next(iter(data[1]["blobs"]))
        data[1]["blobs"][sha] += "changed"
        with self.assertRaises(ValueError):
            report.verify(*data)
        data = minimal_evidence()
        data[1]["execution_events"].pop()
        with self.assertRaises(ValueError):
            report.verify(*data)

    def test_missing_criterion_is_not_silently_dropped(self):
        data = minimal_evidence()
        data[2]["runs"][0]["requirements"].pop()
        with self.assertRaises(ValueError):
            report.verify(*data)

    def test_validation_record_cannot_reference_absent_bytes(self):
        data = minimal_evidence()
        data[1]["validation_records"] = [{"id": "calibration", "blob_sha256": "missing"}]
        with self.assertRaises(ValueError):
            report.verify(*data)

    def test_measurement_history_and_receipts_require_retained_bytes(self):
        data = minimal_evidence()
        data[1]["measurement_history"] = [{"path": "v1/checker.py", "blob_sha256": "absent"}]
        with self.assertRaises(ValueError):
            report.verify(*data)
        data = minimal_evidence()
        add_receipt(data)
        report.verify(*data)
        data[1]["deterministic_receipts"]["R01"]["v2_blob_sha256"] = "absent"
        with self.assertRaises(ValueError):
            report.verify(*data)

    def test_receipt_for_other_output_cannot_unlock_delivery(self):
        data = minimal_evidence()
        add_receipt(data)
        sha = report.digest(b"different answer")
        data[1]["blobs"][sha] = "different answer"
        data[1]["runs"][0]["output_files"]["answer.md"] = sha
        with self.assertRaisesRegex(ValueError, "different output bytes"):
            report.verify(*data)

    def test_unresolved_red_suite_is_not_lost_in_criterion_counts(self):
        data = minimal_evidence()
        add_receipt(data, suite_status="not_verified")
        report.verify(*data)
        data[2]["runs"][0]["requirements"] = requirements("met", "met")
        with self.assertRaisesRegex(ValueError, "Unresolved submitted-suite"):
            report.verify(*data)

    def test_incomplete_allocation_cannot_be_delivered_success(self):
        data = minimal_evidence()
        data[1]["runs"][0]["status"] = "interrupted"
        data[2]["runs"][0]["requirements"] = requirements("met", "met")
        with self.assertRaises(ValueError):
            report.verify(*data)

    def test_restoration_cannot_escape_or_use_ambiguous_paths(self):
        for path in (".", "", "../escape", "/absolute", "a/../escape", "a\\b", "C:/drive", "a//b"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                report.safe_relative(path)
        self.assertEqual("evidence/check.json", str(report.safe_relative("evidence/check.json")))

    def test_restore_accepts_new_nested_path_and_preserves_existing_work(self):
        _, data, _, _ = minimal_evidence()
        run = data["runs"][0]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "new" / "nested" / "work"
            self.assertEqual(2, report.materialize(run, data["blobs"], target))
            self.assertEqual(b"answer", (target / "answer.md").read_bytes())
            with self.assertRaises(ValueError):
                report.materialize(run, data["blobs"], target)
            self.assertEqual(b"answer", (target / "answer.md").read_bytes())

    def test_restore_refuses_linked_parent_before_any_creation(self):
        _, data, _, _ = minimal_evidence()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            foreign = root / "foreign"
            foreign.mkdir()
            (foreign / "sentinel").write_bytes(b"preserve")
            linked = root / "linked"
            try:
                linked.symlink_to(foreign, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation unavailable on this host")
            with self.assertRaises(ValueError):
                report.materialize(data["runs"][0], data["blobs"], linked / "missing" / "work")
            self.assertEqual(["sentinel"], sorted(p.name for p in foreign.iterdir()))
            self.assertEqual(b"preserve", (foreign / "sentinel").read_bytes())

    def test_file_directory_and_case_collisions_are_rejected(self):
        for names in (("a", "a/b"), ("Answer.md", "answer.md")):
            data = minimal_evidence()
            sha = next(iter(data[1]["blobs"]))
            data[1]["runs"][0]["output_files"] = {name: sha for name in names}
            with self.subTest(names=names), self.assertRaises(ValueError):
                report.verify(*data)


class PublishedAssessmentControls(unittest.TestCase):
    """Mutation controls against the actual retained record, without execution."""

    @classmethod
    def setUpClass(cls):
        cls.plan = report.read_json("comparison-plan.json")
        cls.evidence = report.read_json("comparison-evidence.json")
        cls.grades = report.read_json("comparison-grades.json")
        cls.rubric = report.read_json("comparison-rubric.json")
        cls.cases = report.read_json("comparison-cases.json")

    def verify(self, *, grades=None, evidence=None):
        return report.verify_assessments(self.plan, evidence or self.evidence,
                                         grades or self.grades, self.rubric, self.cases)

    @staticmethod
    def retain(record, value):
        content = json.dumps(value)
        sha = report.digest(content.encode())
        record["blobs"][sha] = content
        return sha

    def test_complete_published_assessment_and_separate_calibration(self):
        self.assertEqual({"J1", "J2"}, set(self.verify()))
        self.assertEqual(280, self.grades["assessment_summary"]["subjects"]["requirements"])
        self.assertEqual(42, len(self.grades["runs"]))
        self.assertEqual(32, self.grades["assessment_summary"]["calibration"]["J1"]["requirements"])

    def test_omitted_receipts_or_revised_version_cannot_disappear(self):
        evidence = copy.deepcopy(self.evidence)
        del evidence["deterministic_receipts"]
        with self.assertRaisesRegex(ValueError, "mandatory deterministic"):
            self.verify(evidence=evidence)
        evidence = copy.deepcopy(self.evidence)
        del evidence["deterministic_receipts"]["R35"]["v2_blob_sha256"]
        with self.assertRaisesRegex(ValueError, "measurement version"):
            self.verify(evidence=evidence)

    def test_receipt_cannot_name_an_unrelated_existing_blob_as_checker(self):
        evidence = copy.deepcopy(self.evidence)
        reference = evidence["deterministic_receipts"]["R35"]
        receipt = json.loads(evidence["blobs"][reference["v2_blob_sha256"]])
        run = report.keyed(evidence["runs"], "run_id")["R35"]
        receipt["checker_sha256"] = run["output_files"]["answer.md"]
        reference["v2_blob_sha256"] = self.retain(evidence, receipt)
        with self.assertRaisesRegex(ValueError, "another checker"):
            self.verify(evidence=evidence)

    def test_assessment_cannot_use_another_subjects_output(self):
        grades = copy.deepcopy(self.grades)
        provenance = grades["assessment_provenance"]
        mapping = json.loads(grades["blobs"][provenance["mapping_sha256"]])
        label = next(label for label, run in mapping["mapping"].items() if run == "R35")
        other = report.keyed(self.evidence["runs"], "run_id")["R36"]
        mapping["packet_digests"][label]["work/answer.md"] = other["output_files"]["answer.md"]
        provenance["mapping_sha256"] = self.retain(grades, mapping)
        with self.assertRaisesRegex(ValueError, "different work/"):
            self.verify(grades=grades)

    def test_forged_calibration_score_and_subject_denominator_are_rejected(self):
        grades = copy.deepcopy(self.grades)
        grades["assessment_summary"]["calibration"]["J1"]["matched"] += 1
        with self.assertRaisesRegex(ValueError, "sensitivity or calibration"):
            self.verify(grades=grades)
        grades = copy.deepcopy(self.grades)
        provenance = grades["assessment_provenance"]
        mapping = json.loads(grades["blobs"][provenance["mapping_sha256"]])
        mapping["subject_run_ids"].append(mapping["calibration_control_ids"][0])
        provenance["mapping_sha256"] = self.retain(grades, mapping)
        with self.assertRaisesRegex(ValueError, "populations changed"):
            self.verify(grades=grades)

    def test_changed_consensus_requires_an_explicit_adjudication(self):
        grades = copy.deepcopy(self.grades)
        run = report.keyed(grades["runs"], "run_id")["R35"]
        criterion = run["requirements"][0]
        criterion["status"] = "refuted"
        grades["adjudications"] = [row for row in grades["adjudications"]
                                  if (row["run_id"], row["criterion_id"]) != ("R35", criterion["id"])]
        with self.assertRaisesRegex(ValueError, "Unrecorded disagreement or changed consensus"):
            self.verify(grades=grades)

    def test_an_unfinished_assessment_cannot_be_presented_as_complete(self):
        grades = copy.deepcopy(self.grades)
        grades["assessment_provenance"]["execution_events"].pop()
        with self.assertRaisesRegex(ValueError, "assessment execution observation"):
            self.verify(grades=grades)

    def test_assessment_manifest_cannot_point_to_another_packet(self):
        for replacement in ("sibling", "foreign-root", "relative", "traversal"):
            grades = copy.deepcopy(self.grades)
            provenance = grades["assessment_provenance"]
            record = report.keyed(provenance["assessments"], "assessment_id")["J1"]
            manifest = json.loads(grades["blobs"][record["manifest_sha256"]])
            entry = manifest["packets"][0]
            original = report.PurePosixPath(entry["packet"])
            entry["packet"] = {
                "sibling": str(original.parent / manifest["packets"][1]["label"]),
                "foreign-root": "/different/packets/" + entry["label"],
                "relative": "packets/" + entry["label"],
                "traversal": str(original.parent) + "/other/../" + entry["label"],
            }[replacement]
            sha = self.retain(grades, manifest)
            record["manifest_sha256"] = sha
            record["retained_files"]["manifest.json"] = sha
            mapping = json.loads(grades["blobs"][provenance["mapping_sha256"]])
            mapping["assessments"]["J1"]["manifest_sha256"] = sha
            provenance["mapping_sha256"] = self.retain(grades, mapping)
            with self.subTest(replacement=replacement), self.assertRaisesRegex(ValueError, "[Aa]ssessment.*path"):
                self.verify(grades=grades)


class PublishedPublicationControls(unittest.TestCase):
    """Keep public normalization separate from the captured measurements."""

    @classmethod
    def setUpClass(cls):
        cls.plan, cls.evidence, cls.grades, cls.rubric = report.load_verified()

    def test_public_copy_preserves_original_measurements_and_assessments(self):
        changed = report.publication_changes(self.evidence)
        self.assertEqual(12, len(changed))
        self.assertEqual(7, len(report.publication_changes(self.grades)))
        self.assertEqual(["R08", "R13", "R14", "R15", "R16"],
                         [r["run_id"] for r in self.evidence["runs"] if "published_output_utf8_bytes" in r])
        report.verify_publication_files(self.evidence, self.grades)

    def test_original_and_public_sizes_cannot_be_interchanged(self):
        for field in ("output_utf8_bytes", "answer_utf8_bytes", "published_output_utf8_bytes", "published_answer_utf8_bytes"):
            evidence = copy.deepcopy(self.evidence)
            run = report.keyed(evidence["runs"], "run_id")["R13"]
            run[field] += 1
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "byte count"):
                report.verify(self.plan, evidence, self.grades, self.rubric)

    def test_transform_map_requires_declared_sizes_and_nonoverlapping_offsets(self):
        evidence = copy.deepcopy(self.evidence)
        change = evidence["publication"]["blob_changes"][0]
        change["original_utf8_bytes"] += 1
        with self.assertRaisesRegex(ValueError, "size change"):
            report.publication_changes(evidence)
        evidence = copy.deepcopy(self.evidence)
        change = evidence["publication"]["blob_changes"][0]
        change["locations"].append(copy.deepcopy(change["locations"][0]))
        with self.assertRaisesRegex(ValueError, "overlap"):
            report.publication_changes(evidence)

    def test_publication_manifest_cannot_drop_original_or_file_bindings(self):
        original = report.read_json("comparison-publication.json")
        for field in ("original_sha256", "published_sha256", "original_utf8_bytes", "published_utf8_bytes"):
            manifest = copy.deepcopy(original)
            del manifest["files"]["comparison-evidence.json"][field]
            with self.subTest(field=field), patch.object(report, "read_json", return_value=manifest), self.assertRaisesRegex(ValueError, "transformation manifest"):
                report.verify_publication_files(self.evidence, self.grades)

    def test_publication_cannot_hide_or_forge_normalization_details(self):
        original = report.read_json("comparison-publication.json")
        for fault in ("omit-metadata", "omit-rules", "wrong-count", "wrong-value"):
            manifest = copy.deepcopy(original)
            if fault == "omit-metadata":
                manifest["metadata_changes"] = []
            elif fault == "omit-rules":
                manifest["rules"] = []
            elif fault == "wrong-count":
                manifest["rules"][0]["occurrences"] = 1
            else:
                manifest["metadata_changes"][0]["published_sha256"] = "0" * 64
            with self.subTest(fault=fault), patch.object(report, "read_json", return_value=manifest), self.assertRaises(ValueError):
                report.verify_publication_files(self.evidence, self.grades)


if __name__ == "__main__":
    unittest.main()
