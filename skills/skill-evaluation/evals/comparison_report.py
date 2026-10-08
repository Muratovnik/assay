"""Verify retained comparison evidence and reproduce descriptive results.

This utility does not launch or grade models and does not execute saved outputs.
`materialize RUN OUTPUT` restores one retained work directory into a new path.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat


HERE = Path(__file__).resolve().parent
STATUSES = {"met", "refuted", "not_verified"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def keyed(records, field):
    if not isinstance(records, list) or not records:
        raise ValueError(f"Expected a nonempty list of {field} records")
    result = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError(f"Invalid {field} record")
        key = record[field]
        if key in result:
            raise ValueError(f"Duplicate {field}: {key}")
        result[key] = record
    return result


def safe_relative(name):
    if not isinstance(name, str):
        raise ValueError("Artifact path must be a string")
    path = PurePosixPath(name)
    if not path.parts or path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name or str(path) != name:
        raise ValueError(f"Unsafe or noncanonical artifact path: {name!r}")
    return path


def inventory(files, blobs, label, *, allow_empty=False):
    if not isinstance(files, dict) or (not files and not allow_empty):
        raise ValueError(f"Invalid file inventory: {label}")
    folded = set()
    for name, sha in files.items():
        safe_relative(name)
        if name.casefold() in folded:
            raise ValueError(f"Case-colliding artifact path: {label}/{name}")
        folded.add(name.casefold())
        if not isinstance(sha, str) or sha not in blobs:
            raise ValueError(f"Missing retained bytes: {label}/{name}")
    for name in files:
        if any(parent.as_posix().casefold() in folded for parent in PurePosixPath(name).parents if parent != PurePosixPath(".")):
            raise ValueError(f"File/directory collision: {label}/{name}")


def publication_changes(record):
    """Validate a reviewed derivative's map without claiming access to its original."""
    if "publication" not in record:
        return {}
    publication = record["publication"]
    if not isinstance(publication, dict) or publication.get("schema_version") != 1 or publication.get("kind") != "reviewed-publication-derivative":
        raise ValueError("Invalid publication provenance")
    if publication.get("manifest_file") != "comparison-publication.json":
        raise ValueError("Unexpected publication manifest")

    def valid_sha(value):
        return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)

    def valid_size(value):
        return type(value) is int and value >= 0

    if not valid_sha(publication.get("original_sha256")) or not valid_size(publication.get("original_utf8_bytes")):
        raise ValueError("Missing private-original publication identity")
    blobs = record["blobs"]
    if type(publication.get("original_blob_count")) is not int or publication["original_blob_count"] != len(blobs):
        raise ValueError("Publication blob population changed")
    changes = publication.get("blob_changes")
    if not isinstance(changes, list) or not changes:
        raise ValueError("Missing publication transformation records")
    published = keyed(changes, "published_sha256")
    keyed(changes, "original_sha256")
    allowed = {"task-identifier-normalization", "home-cache-redaction", "digest-rebind"}
    for sha, row in published.items():
        if not valid_sha(sha) or not valid_sha(row["original_sha256"]) or sha == row["original_sha256"] or sha not in blobs:
            raise ValueError("Invalid transformed publication blob identity")
        if not valid_size(row.get("original_utf8_bytes")) or not valid_size(row.get("published_utf8_bytes")):
            raise ValueError("Missing original/published byte measurements")
        if row["published_utf8_bytes"] != len(blobs[sha].encode("utf-8")):
            raise ValueError("Publication blob byte count differs")
        categories, locations = row.get("categories"), row.get("locations")
        if not isinstance(categories, list) or not categories or any(c not in allowed for c in categories):
            raise ValueError("Unreviewed publication transformation category")
        if not isinstance(locations, list) or not locations or any(not isinstance(p, dict) for p in locations):
            raise ValueError("Missing publication transformation location")
        if set(categories) != {p.get("kind") for p in locations}:
            raise ValueError("Publication locations use different categories")
        intervals, delta = [], 0
        for location in locations:
            start = location.get("original_byte_offset")
            if not valid_size(start):
                raise ValueError("Invalid publication byte offset")
            if location["kind"] == "digest-rebind":
                if not valid_sha(location.get("original_sha256")) or not valid_sha(location.get("published_sha256")):
                    raise ValueError("Invalid publication digest rebinding")
                length = 64
            else:
                length, replacement = location.get("original_utf8_bytes"), location.get("published_utf8_bytes")
                if not valid_size(length) or length == 0 or not valid_size(replacement) or not isinstance(location.get("rule_id"), str):
                    raise ValueError("Invalid reviewed prefix replacement")
                delta += replacement - length
            intervals.append((start, start + length))
        intervals.sort()
        if any(end > row["original_utf8_bytes"] for _, end in intervals) or any(a[1] > b[0] for a, b in zip(intervals, intervals[1:])):
            raise ValueError("Publication replacements overlap or exceed original bytes")
        if row["original_utf8_bytes"] + delta != row["published_utf8_bytes"]:
            raise ValueError("Publication size change differs from declared replacements")
    return published


def verify_publication_files(evidence, grades):
    """Verify the public derivative; original-byte replay remains a private check."""
    documents = {"comparison-evidence.json": evidence, "comparison-grades.json": grades}
    present = ["publication" in record for record in documents.values()]
    if not any(present):
        return
    if not all(present):
        raise ValueError("Incomplete publication derivative provenance")
    manifest = read_json("comparison-publication.json")
    if manifest.get("schema_version") != 1 or manifest.get("kind") != "reviewed-publication-derivative" or set(manifest["files"]) != set(documents):
        raise ValueError("Invalid publication file manifest")
    combined, by_file = {}, {}
    for name, record in documents.items():
        raw = (HERE / name).read_bytes()
        publication = record["publication"]
        expected = {"original_sha256": publication["original_sha256"],
                    "published_sha256": digest(raw),
                    "original_utf8_bytes": publication["original_utf8_bytes"],
                    "published_utf8_bytes": len(raw)}
        if manifest["files"][name] != expected:
            raise ValueError(f"Published file differs from its transformation manifest: {name}")
        changes = publication_changes(record)
        by_file[name] = len(changes)
        if any(sha in combined and combined[sha] != row for sha, row in changes.items()):
            raise ValueError("Conflicting publication transformation maps")
        combined.update(changes)
    if keyed(manifest["blob_changes"], "published_sha256") != combined:
        raise ValueError("External publication blob map differs")
    rules = keyed(manifest["rules"], "id")
    replacements = {"task-identifier-normalization": ("agent:", ["trial_", "assessment_"]),
                    "home-cache-redaction": ("[PLAYWRIGHT_CACHE]/", None)}
    if len(rules) != 2 or {r.get("kind") for r in rules.values()} != set(replacements):
        raise ValueError("Missing reviewed publication rules")
    for rule in rules.values():
        prefix, following = replacements[rule["kind"]]
        source_sha = rule.get("source_prefix_sha256")
        if rule.get("published_prefix") != prefix or rule.get("following_name_prefixes") != following:
            raise ValueError("Publication replacement rules changed")
        if not isinstance(source_sha, str) or len(source_sha) != 64 or any(c not in "0123456789abcdef" for c in source_sha):
            raise ValueError("Missing private publication-prefix commitment")
        if any(type(rule.get(key)) is not int or rule[key] <= 0 for key in ("source_prefix_utf8_bytes", "occurrences")):
            raise ValueError("Invalid publication rule measurements")
    strings = {}

    def leaves(value, path):
        if isinstance(value, dict):
            for key, item in value.items():
                leaves(item, path + "." + key)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                leaves(item, f"{path}[{index}]")
        elif isinstance(value, str):
            if path in strings:
                raise ValueError("Ambiguous publication metadata path")
            strings[path] = value

    for name, document in documents.items():
        leaves({k: v for k, v in document.items() if k not in {"blobs", "publication"}}, name)
    metadata = keyed(manifest["metadata_changes"], "path")
    markers = [r["published_prefix"] + name for r in rules.values()
               for name in (r["following_name_prefixes"] or [""])]
    expected_metadata = {path for path, value in strings.items()
                         if any(marker in value for marker in markers) or any(sha in value for sha in combined)}
    if set(metadata) != expected_metadata:
        raise ValueError("Publication metadata transformation inventory differs")
    occurrences = Counter()
    old_to_new = {row["original_sha256"]: sha for sha, row in combined.items()}

    def locations(row, content):
        edits = row.get("locations")
        if not isinstance(edits, list) or not edits or any(not isinstance(e, dict) for e in edits):
            raise ValueError("Missing publication replacement locations")
        if type(row.get("original_utf8_bytes")) is not int or row["original_utf8_bytes"] < 0:
            raise ValueError("Invalid original publication string size")
        if any(type(e.get("original_byte_offset")) is not int or e["original_byte_offset"] < 0 for e in edits):
            raise ValueError("Invalid publication metadata offset")
        offset_delta, previous_end = 0, 0
        for edit in sorted(edits, key=lambda e: e["original_byte_offset"]):
            start = edit["original_byte_offset"]
            if edit.get("kind") == "digest-rebind":
                original, published = edit.get("original_sha256"), edit.get("published_sha256")
                if not isinstance(original, str) or old_to_new.get(original) != published:
                    raise ValueError("Publication metadata digest rebinding differs")
                length, replacement = 64, published.encode("ascii")
            else:
                rule = rules.get(edit.get("rule_id"))
                if rule is None or edit.get("kind") != rule["kind"]:
                    raise ValueError("Publication location uses an unreviewed rule")
                length = rule["source_prefix_utf8_bytes"]
                replacement = rule["published_prefix"].encode("utf-8")
                if edit.get("original_utf8_bytes") != length or edit.get("published_utf8_bytes") != len(replacement):
                    raise ValueError("Publication location differs from its rule")
                occurrences[rule["id"]] += 1
            if start < previous_end or start + length > row["original_utf8_bytes"]:
                raise ValueError("Publication metadata edits overlap or exceed their input")
            actual_start = start + offset_delta
            if content[actual_start:actual_start + len(replacement)] != replacement:
                raise ValueError("Publication replacement is absent from its declared location")
            offset_delta += len(replacement) - length
            previous_end = start + length
        if row["original_utf8_bytes"] + offset_delta != len(content):
            raise ValueError("Publication metadata size change differs")

    for path, row in metadata.items():
        content = strings[path].encode("utf-8")
        if row.get("published_sha256") != digest(content) or row.get("published_utf8_bytes") != len(content):
            raise ValueError("Publication metadata does not bind its published value")
        source_sha = row.get("original_sha256")
        if not isinstance(source_sha, str) or len(source_sha) != 64 or any(c not in "0123456789abcdef" for c in source_sha):
            raise ValueError("Missing original metadata commitment")
        locations(row, content)
    all_blobs = {**evidence["blobs"], **grades["blobs"]}
    for sha, row in combined.items():
        locations(row, all_blobs[sha].encode("utf-8"))
    if dict(occurrences) != {key: row["occurrences"] for key, row in rules.items()}:
        raise ValueError("Publication rule occurrence counts differ")
    for name, identity in manifest["preserved_inputs"].items():
        safe_relative(name)
        raw = (HERE / name).read_bytes()
        if identity != {"sha256": digest(raw), "utf8_bytes": len(raw)}:
            raise ValueError(f"Publication changed a preserved study input: {name}")
    if set(manifest["preserved_inputs"]) != {"comparison-plan.json", "comparison-cases.json", "comparison-rubric.json", "comparison-case-metadata.json", "comparison-protocol.md"}:
        raise ValueError("Publication preserved-input inventory changed")
    if manifest["transformer_sha256"] != digest((HERE / "comparison_publication.py").read_bytes()):
        raise ValueError("Publication transformer identity changed")
    checks = manifest["preservation_checks"]
    blob_count = len(set(evidence["blobs"]) | set(grades["blobs"]))
    affected = [r["run_id"] for r in evidence["runs"] if "published_output_utf8_bytes" in r]
    expected_checks = {
        "original_blob_count": blob_count, "changed_blob_count": len(combined),
        "unchanged_blob_count": blob_count - len(combined), "changed_by_file": by_file,
        "affected_output_run_ids": affected, "original_observed_byte_metrics_preserved": True,
        "source_file_inventories_preserved": True, "deterministic_receipt_identities_preserved": True,
        "assessment_output_sha256": {r["assessment_id"]: r["output_sha256"] for r in grades["assessment_provenance"]["assessments"]},
        "final_grading_and_adjudication_values_preserved": True,
    }
    if checks != expected_checks:
        raise ValueError("Publication preservation accounting differs")
    expected_rebinding = [{"path": "comparison-grades.json.evidence_sha256",
                           "original_sha256": evidence["publication"]["original_sha256"],
                           "published_sha256": grades["evidence_sha256"]}]
    if manifest["file_digest_rebindings"] != expected_rebinding:
        raise ValueError("Publication file-identity rebinding differs")


def design_population(plan, rubric):
    """Reject lost task groups, duplicate identities and empty evidence."""
    planned = keyed(plan["trials"], "run_id")
    blocks = keyed(plan["blocks"], "id")
    cases = keyed(rubric["cases"], "id")
    criteria = {}
    for case_id, case in cases.items():
        criteria[case_id] = keyed(case["requirements"], "id")
        for criterion in criteria[case_id].values():
            if criterion.get("weight", 1) != 1:
                raise ValueError("Only the declared unweighted atomic requirements are supported")
    expected_cases = {}
    for block_id, block in blocks.items():
        skills = block["skills"]
        if not isinstance(skills, list) or len(skills) != 2 or any(not isinstance(s, str) or not s for s in skills) or len(set(skills)) != 2:
            raise ValueError(f"Invalid method pair: {block_id}")
        for field, suffix, arms in (("main_case", "-M", {"00", "10", "01", "11"}),
                                    ("control_case", "-C", {"00", "11"})):
            case_id = block[field]
            if not isinstance(case_id, str) or not case_id.endswith(suffix) or case_id in expected_cases:
                raise ValueError(f"Invalid or repeated declared case: {block_id}/{field}")
            expected_cases[case_id] = (block_id, arms)
    if set(cases) != set(expected_cases):
        raise ValueError("Declared task groups and fixed rubric inventory differ")
    observed = {case: set() for case in expected_cases}
    for run_id, trial in planned.items():
        case_id, arm = trial["case_id"], trial["arm"]
        if case_id not in expected_cases:
            raise ValueError(f"Undeclared task allocation: {run_id}")
        block_id, arms = expected_cases[case_id]
        if trial["block"] != block_id or arm not in arms or arm in observed[case_id]:
            raise ValueError(f"Wrong or duplicate condition: {run_id}")
        observed[case_id].add(arm)
        pair = blocks[block_id]["skills"]
        expected_skills = [pair[i] for i, enabled in enumerate(arm) if enabled == "1"]
        if trial["skills"] != expected_skills:
            raise ValueError(f"Condition/method identity changed: {run_id}")
    if any(observed[case] != arms for case, (_, arms) in expected_cases.items()):
        raise ValueError("A declared task or comparison condition is missing")
    return planned, criteria


def outcome(requirements):
    if not isinstance(requirements, list) or any(not isinstance(r, dict) or not isinstance(r.get("status"), str) for r in requirements):
        raise ValueError("Invalid requirement records")
    counts = Counter(record["status"] for record in requirements)
    if set(counts) - STATUSES:
        raise ValueError("Unrecognized requirement status")
    if not requirements:
        raise ValueError("No requirements; no vacuous success")
    total = len(requirements)
    met, refuted, unknown = (counts[name] for name in ("met", "refuted", "not_verified"))
    strict = "refuted" if refuted else "not_verified" if unknown else "met"
    return {
        "met": met, "refuted": refuted, "not_verified": unknown,
        "requirements": total, "strict": strict,
        "requirement_fraction": met / total if not unknown else None,
        "requirement_fraction_interval": [met / total, (met + unknown) / total],
        "strict_interval": [int(strict == "met"), int(strict != "refuted")],
    }


def linear_contrast(arms, coefficients):
    """Conservative bounds; unobserved requirements are never imputed as zero."""
    low = high = 0
    for arm, coefficient in coefficients.items():
        lower, upper = arms[arm]["requirement_fraction_interval"]
        low += coefficient * (lower if coefficient >= 0 else upper)
        high += coefficient * (upper if coefficient >= 0 else lower)
    return {"value": low if low == high else None, "interval": [low, high]}


def verify_measurement_receipts(evidence, runs, scored):
    blobs = evidence["blobs"]
    history = evidence.get("measurement_history", [])
    if not isinstance(history, list):
        raise ValueError("Invalid measurement history")
    if history:
        keyed(history, "path")
    for record in history:
        safe_relative(record["path"])
        if record["blob_sha256"] not in blobs:
            raise ValueError(f"Missing measurement-history bytes: {record['path']}")
    receipts = evidence.get("deterministic_receipts", {})
    if not isinstance(receipts, dict):
        raise ValueError("Invalid deterministic-receipt collection")
    for run_id, versions in receipts.items():
        if run_id not in runs or not isinstance(versions, dict) or not versions or set(versions) - {"v1_blob_sha256", "v2_blob_sha256"}:
            raise ValueError(f"Invalid deterministic-receipt identity: {run_id}")
        observed = {}
        for version, sha in versions.items():
            if sha not in blobs:
                raise ValueError(f"Missing deterministic receipt: {run_id}/{version}")
            receipt = json.loads(blobs[sha])
            if not isinstance(receipt, dict) or receipt.get("run_id") != run_id or receipt.get("case") != runs[run_id]["case_id"]:
                raise ValueError(f"Receipt describes another subject: {run_id}/{version}")
            if receipt["checker_sha256"] not in blobs:
                raise ValueError(f"Missing executed checker bytes: {run_id}/{version}")
            expected = digest(json.dumps(runs[run_id]["output_files"], sort_keys=True).encode("utf-8"))
            if receipt.get("subject_inventory_sha256") != expected:
                raise ValueError(f"Receipt belongs to different output bytes: {run_id}/{version}")
            if receipt.get("evaluator_preserved_subject_bytes") is not True:
                raise ValueError(f"Evaluator preservation not established: {run_id}/{version}")
            recorded = keyed(receipt["criteria"], "id")
            if set(recorded) != set(keyed(scored[run_id]["requirements"], "id")):
                raise ValueError(f"Receipt uses different criteria: {run_id}/{version}")
            outcome(receipt["criteria"])
            observed[version] = receipt
        current = observed.get("v2_blob_sha256", observed.get("v1_blob_sha256"))
        assessment = current["evidence"].get("submitted_suite_assessment")
        if assessment is not None:
            if not isinstance(assessment, dict) or assessment.get("status") not in STATUSES:
                raise ValueError(f"Invalid submitted-suite assessment: {run_id}")
            # This is contradictory evidence about delivery, not a ninth point
            # in the rubric. A per-criterion total must not erase that barrier.
            if assessment["status"] != "met" and outcome(scored[run_id]["requirements"])["strict"] == "met":
                raise ValueError(f"Unresolved submitted-suite evidence cannot certify delivery: {run_id}")


def verify(plan, evidence, grades, rubric):
    planned, criteria = design_population(plan, rubric)
    runs = keyed(evidence["runs"], "run_id")
    scored = keyed(grades["runs"], "run_id")
    if set(runs) != set(planned) or set(scored) != set(planned):
        raise ValueError("Every planned allocation must remain in both evidence and grading")
    blobs = evidence["blobs"]
    if not isinstance(blobs, dict) or not blobs:
        raise ValueError("No retained evidence blobs")
    for sha, content in blobs.items():
        if not isinstance(content, str) or digest(content.encode("utf-8")) != sha:
            raise ValueError(f"Retained UTF-8 blob does not match its digest: {sha}")
    published_changes = publication_changes(evidence)
    validation = evidence.get("validation_records", [])
    if not isinstance(validation, list) or any(not isinstance(row, dict) for row in validation):
        raise ValueError("Invalid validation records")
    if validation:
        keyed(validation, "id")
    for row in validation:
        if row["blob_sha256"] not in blobs:
            raise ValueError(f"Missing retained validation bytes: {row['id']}")
    implementations = evidence.get("implementation_blobs", {})
    if not isinstance(implementations, dict):
        raise ValueError("Invalid implementation references")
    for name, sha in implementations.items():
        safe_relative(name)
        if sha not in blobs:
            raise ValueError(f"Missing retained measurement implementation: {name}")
    observations = evidence["execution_events"]
    if not isinstance(observations, list) or any(not isinstance(row, dict) for row in observations):
        raise ValueError("Invalid execution observations")
    events = Counter()
    for row in observations:
        if row.get("run_id") not in planned or row.get("event") not in {"spawn_observed", "completion_observed"}:
            raise ValueError("Unknown execution event or allocation")
        events[row["run_id"], row["event"]] += 1
    if any(count != 1 for count in events.values()):
        raise ValueError("Duplicate execution observation")
    for run_id, planned_run in planned.items():
        run, grade = runs[run_id], scored[run_id]
        if run["case_id"] != planned_run["case_id"]:
            raise ValueError(f"Task identity changed: {run_id}")
        for record in (run, grade):
            for field in ("case_id", "arm", "skills", "block"):
                if field in record and record[field] != planned_run[field]:
                    raise ValueError(f"Contradictory {field}: {run_id}")
        if grade.get("case_id") != planned_run["case_id"] or grade.get("arm") != planned_run["arm"]:
            raise ValueError(f"Missing grade identity: {run_id}")
        if run["status"] not in {"planned", "completed", "interrupted", "cancelled", "failed"}:
            raise ValueError(f"Unknown allocation status: {run_id}")
        manifest_sha = planned_run["packet_manifest_sha256"]
        manifest = json.loads(blobs[manifest_sha])
        if not isinstance(manifest, dict):
            raise ValueError(f"Invalid packet manifest: {run_id}")
        if manifest["case_id"] != run["case_id"] or manifest["files"] != planned_run["packet_files"]:
            raise ValueError(f"Packet manifest changed: {run_id}")
        if manifest["source_sha256"] != plan["input_digests"]["comparison-cases.json"]:
            raise ValueError(f"Input collection identity changed: {run_id}")
        inventory(planned_run["packet_files"], blobs, f"{run_id}/packet")
        method_names = {PurePosixPath(name).parts[1] for name in planned_run["packet_files"] if name.startswith("skill/") and len(PurePosixPath(name).parts) > 2}
        if method_names != set(planned_run["skills"]):
            raise ValueError(f"Packet contains the wrong methods: {run_id}")
        if planned_run["launch_sha256"] not in blobs:
            raise ValueError(f"Missing exact launch instructions: {run_id}")
        inventory(run["output_files"], blobs, f"{run_id}/work", allow_empty=run["status"] != "completed")
        inputs = {name.removeprefix("inputs/"): sha for name, sha in planned_run["packet_files"].items() if name.startswith("inputs/")}
        if run.get("source_files") != inputs:
            raise ValueError(f"Captured source identity changed: {run_id}")
        changed = sorted(name for name, sha in inputs.items() if run["output_files"].get(name) != sha)
        added = sorted(set(run["output_files"]) - set(inputs))
        if run.get("changed_source_files") != changed or run.get("new_files") != added:
            raise ValueError(f"Captured change inventory is inconsistent: {run_id}")
        outputs = list(run["output_files"].values())
        answer = [run["output_files"]["answer.md"]] if "answer.md" in run["output_files"] else []
        changed_for_publication = any(sha in published_changes for sha in outputs)
        for name, selected in (("output_utf8_bytes", outputs), ("answer_utf8_bytes", answer)):
            total = sum(len(blobs[sha].encode("utf-8")) for sha in selected)
            original_total = sum(published_changes[sha]["original_utf8_bytes"] if sha in published_changes
                                 else len(blobs[sha].encode("utf-8")) for sha in selected)
            if name in run and run[name] != original_total:
                raise ValueError(f"Incorrect retained byte count: {run_id}/{name}")
            field = "published_" + name
            if changed_for_publication and run.get(field) != total:
                raise ValueError(f"Incorrect published byte count: {run_id}/{field}")
            if not changed_for_publication and field in run:
                raise ValueError(f"Unexplained publication byte count: {run_id}/{field}")
        if run["status"] == "completed":
            if "answer.md" not in run["output_files"]:
                raise ValueError(f"Completed run lacks its required answer: {run_id}")
            for event in ("spawn_observed", "completion_observed"):
                if events[run_id, event] != 1:
                    raise ValueError(f"Missing or duplicate execution observation: {run_id}/{event}")
        requirements = keyed(grade["requirements"], "id")
        if set(requirements) != set(criteria[run["case_id"]]):
            raise ValueError(f"Missing or unexpected criteria: {run_id}")
        for record in requirements.values():
            if not isinstance(record.get("status"), str) or record["status"] not in STATUSES or not isinstance(record.get("evidence"), str) or not record["evidence"].strip():
                raise ValueError(f"Invalid or unsupported grade: {run_id}/{record['id']}")
        if run["status"] != "completed" and outcome(grade["requirements"])["strict"] == "met":
            raise ValueError(f"Incomplete allocation cannot be a strict delivered success: {run_id}")
    verify_measurement_receipts(evidence, runs, scored)
    return planned, runs, scored


def summarize(plan, evidence, grades, rubric):
    planned, runs, scored = verify(plan, evidence, grades, rubric)
    by_case = {}
    for run_id, row in planned.items():
        arms = by_case.setdefault(row["case_id"], {})
        if row["arm"] in arms:
            raise ValueError(f"Duplicate single-trial condition: {row['case_id']}/{row['arm']}")
        arms[row["arm"]] = {"run_id": run_id, **outcome(scored[run_id]["requirements"])}
    comparisons = {}
    for case, arms in sorted(by_case.items()):
        expected = {"00", "11"} if case.endswith("-C") else {"00", "10", "01", "11"}
        if set(arms) != expected:
            raise ValueError(f"Missing planned comparison condition: {case}")
        formulas = {"bundle_minus_none": {"11": 1, "00": -1}}
        if "10" in arms:
            formulas.update({
                "A_minus_none": {"10": 1, "00": -1},
                "B_minus_none": {"01": 1, "00": -1},
                "B_added_to_A": {"11": 1, "10": -1},
                "A_added_to_B": {"11": 1, "01": -1},
                "interaction": {"11": 1, "10": -1, "01": -1, "00": 1},
            })
        comparisons[case] = {"arms": arms, "contrasts": {
            name: linear_contrast(arms, coefficients) for name, coefficients in formulas.items()}}
    return {
        "schema_version": 1,
        "allocation_counts": dict(sorted(Counter(row["status"] for row in runs.values()).items())),
        "assigned": len(planned),
        "interpretation": "Single-trial descriptive requirement contrasts; no variance, population ranking, causal discovery or savings estimate.",
        "comparisons": comparisons,
    }


def assessment_statistics(mapping, calibration, assessments):
    """Raw sensitivity and known-control agreement; no majority-vote oracle."""
    inverse = {identity: label for label, identity in mapping["mapping"].items()}
    names = sorted(assessments)
    if len(names) != 2:
        raise ValueError("This measurement declares exactly two assessments")
    indexed = {name: {label: keyed(row["requirements"], "id") for label, row in rows.items()}
               for name, rows in assessments.items()}
    pairs, disagreements = Counter(), []
    for run_id in mapping["subject_run_ids"]:
        label = inverse[run_id]
        for criterion in indexed[names[0]][label]:
            statuses = {name: indexed[name][label][criterion]["status"] for name in names}
            pairs["/".join(statuses.values())] += 1
            if len(set(statuses.values())) != 1:
                disagreements.append({"run_id": run_id, "criterion_id": criterion, "statuses": statuses})
    calibration_results = {}
    for name in names:
        mismatches, total = [], 0
        for control in calibration["controls"]:
            for expected in control["expected_requirements"]:
                total += 1
                actual = indexed[name][inverse[control["id"]]][expected["id"]]["status"]
                if actual != expected["status"]:
                    mismatches.append({"control_id": control["id"], "criterion_id": expected["id"],
                                       "expected": expected["status"], "observed": actual})
        calibration_results[name] = {"requirements": total, "matched": total - len(mismatches), "mismatches": mismatches}
    return {"subjects": {"requirements": sum(pairs.values()),
                         "matching_statuses": sum(pairs.values()) - len(disagreements),
                         "status_pairs": dict(sorted(pairs.items())), "disagreements": disagreements},
            "calibration": calibration_results}


def verify_assessments(plan, evidence, grades, rubric, cases):
    """Bind judgments to the same blinded packets and preserve adjudication."""
    extra = grades["blobs"]
    if not isinstance(extra, dict) or not extra:
        raise ValueError("Missing retained assessment bytes")
    for sha, content in extra.items():
        if not isinstance(content, str) or digest(content.encode("utf-8")) != sha:
            raise ValueError(f"Assessment blob digest mismatch: {sha}")
        if sha in evidence["blobs"] and evidence["blobs"][sha] != content:
            raise ValueError("Conflicting retained blob content")
    blobs = {**evidence["blobs"], **extra}

    def document(sha):
        if not isinstance(sha, str) or sha not in blobs:
            raise ValueError("Missing assessment source bytes")
        value = json.loads(blobs[sha])
        if not isinstance(value, dict):
            raise ValueError("Assessment documents must be JSON objects")
        return value

    provenance = grades["assessment_provenance"]
    if not isinstance(provenance, dict):
        raise ValueError("Invalid assessment provenance")
    mapping = document(provenance["mapping_sha256"])
    calibration = document(provenance["calibration_sha256"])
    if mapping["calibration_sha256"] != provenance["calibration_sha256"]:
        raise ValueError("The frozen calibration identity changed")
    if provenance["preparation_sha256"] not in blobs:
        raise ValueError("Missing assessment-preparation implementation")
    inventory(provenance.get("supporting_files", {}), blobs, "assessment-support", allow_empty=True)
    inventory(grades.get("verification_implementation_blobs", {}), blobs, "verification-code", allow_empty=True)
    planned = keyed(plan["trials"], "run_id")
    runs = keyed(evidence["runs"], "run_id")
    expected_receipts = sorted(run_id for run_id, row in planned.items() if row["case_id"] in {"B1-M", "B1-C", "B4-C"})
    history = keyed(evidence["measurement_history"], "path")
    checker_versions = {
        "v1_blob_sha256": history["v1/comparison_checks.py"]["blob_sha256"],
        "v2_blob_sha256": evidence["implementation_blobs"]["comparison_checks.py"],
    }
    policy = provenance["deterministic_policy"]
    if policy != {"run_ids": expected_receipts, "checker_sha256_by_receipt_version": checker_versions}:
        raise ValueError("The declared deterministic-receipt policy changed")
    retained_receipts = evidence.get("deterministic_receipts", {})
    if not isinstance(retained_receipts, dict) or set(retained_receipts) != set(expected_receipts):
        raise ValueError("Missing or unexpected mandatory deterministic receipts")
    for run_id, versions in retained_receipts.items():
        if set(versions) != set(checker_versions):
            raise ValueError(f"A mandatory measurement version is absent: {run_id}")
        for version, sha in versions.items():
            if document(sha)["checker_sha256"] != checker_versions[version]:
                raise ValueError(f"Receipt is attributed to another checker: {run_id}/{version}")
    criteria = {case: keyed(row["requirements"], "id") for case, row in keyed(rubric["cases"], "id").items()}
    sources = keyed(cases["cases"], "id")
    controls = keyed(calibration["controls"], "id")
    subjects = mapping["subject_run_ids"]
    declared_controls = mapping["calibration_control_ids"]
    labels = mapping["mapping"]
    if not isinstance(labels, dict) or not labels or not isinstance(subjects, list) or not isinstance(declared_controls, list):
        raise ValueError("Invalid blinded population")
    if set(subjects) != set(planned) or len(subjects) != len(planned) or set(declared_controls) != set(controls) or len(declared_controls) != len(controls):
        raise ValueError("Subject and calibration populations changed")
    if set(subjects) & set(controls) or len(labels) != len(set(labels.values())) or set(labels.values()) != set(subjects) | set(controls):
        raise ValueError("Blinded labels are not a bijection of subjects and separate controls")
    if set(mapping["packet_digests"]) != set(labels):
        raise ValueError("Missing blinded packet inventory")
    for control in controls.values():
        expected = keyed(control["expected_requirements"], "id")
        if set(expected) != set(criteria[calibration["case_id"]]):
            raise ValueError("Calibration uses different criteria")
        outcome(control["expected_requirements"])
        if not isinstance(control.get("files"), dict) or any(not isinstance(name, str) or not isinstance(content, str) for name, content in control["files"].items()):
            raise ValueError("Invalid constructed control files")
    label_cases = {}
    for label, identity in labels.items():
        safe_relative(label)
        subject = identity in planned
        case_id = planned[identity]["case_id"] if subject else calibration["case_id"]
        label_cases[label] = case_id
        packet = mapping["packet_digests"][label]
        inventory(packet, blobs, f"assessment/{label}")
        source = sources[case_id]
        if not isinstance(source.get("files"), dict) or any(not isinstance(name, str) or not isinstance(content, str) for name, content in source["files"].items()):
            raise ValueError("Invalid task source files")
        expected_task = {key: value for key, value in source.items() if key != "files"}
        if document(packet["task.json"]) != expected_task or document(packet["requirements.json"]) != keyed(rubric["cases"], "id")[case_id]:
            raise ValueError(f"Blinded task or rubric changed: {label}")
        source_files = {name: digest(content.encode("utf-8")) for name, content in source["files"].items()}
        if subject:
            output_files = runs[identity]["output_files"]
        else:
            output_files = {**source_files, **{name: digest(content.encode("utf-8")) for name, content in controls[identity]["files"].items()}}
        expected_files = {"task.json", "requirements.json", "final_inventory.json"}
        for prefix, expected in (("source/", source_files), ("work/", output_files)):
            actual = {name.removeprefix(prefix): sha for name, sha in packet.items() if name.startswith(prefix)}
            if actual != expected:
                raise ValueError(f"Assessment uses different {prefix} bytes: {label}")
            expected_files.update(prefix + name for name in expected)
        observed = document(packet["final_inventory.json"])
        if observed.get("source_files") != source_files or observed.get("output_files") != output_files:
            raise ValueError(f"Blinded final inventory differs: {label}")
        changed = sorted(name for name, sha in source_files.items() if output_files.get(name) != sha)
        if observed.get("changed_source_files") != changed or observed.get("new_files") != sorted(set(output_files) - set(source_files)):
            raise ValueError(f"Blinded change inventory differs: {label}")
        versions = evidence.get("deterministic_receipts", {}).get(identity, {})
        if versions:
            current = document(versions.get("v2_blob_sha256", versions.get("v1_blob_sha256")))
            expected_behavior = {"case": case_id, **{key: current[key] for key in ("evidence", "evaluator_preserved_subject_bytes", "limits", "checker_sha256", "observed_at_utc")}}
            if document(packet["coordinator_behavior.json"]) != expected_behavior:
                raise ValueError(f"Blinded behavior receipt changed: {label}")
            expected_files.add("coordinator_behavior.json")
        if set(packet) != expected_files:
            raise ValueError(f"Unexpected blinded input files: {label}")
    assessments = {}
    records = keyed(provenance["assessments"], "assessment_id")
    if set(records) != set(mapping["assessments"]):
        raise ValueError("Assessment allocation changed")
    events = provenance["execution_events"]
    if not isinstance(events, list) or any(not isinstance(row, dict) for row in events):
        raise ValueError("Invalid assessment completion observations")
    observed_events = Counter((row["assessment_id"], row["event"]) for row in events)
    expected_events = Counter((name, event) for name in records for event in ("spawn_observed", "completion_observed"))
    if observed_events != expected_events:
        raise ValueError("Missing or duplicate assessment execution observation")
    packet_root = None
    packet_paths = {}
    for name, record in records.items():
        declared = mapping["assessments"][name]
        if record["manifest_sha256"] != declared["manifest_sha256"] or record["instruction_sha256"] != declared["instruction_sha256"] or record["instruction_sha256"] not in blobs:
            raise ValueError(f"Assessment instructions or manifest changed: {name}")
        manifest = document(record["manifest_sha256"])
        entries = keyed(manifest["packets"], "label")
        if manifest["assessment_id"] != name or set(entries) != set(labels) or list(entries) != declared["order"]:
            raise ValueError(f"Assessment presentation changed: {name}")
        if any(row["case_id"] != label_cases[label] for label, row in entries.items()):
            raise ValueError(f"Manifest task identity changed: {name}")
        for label, row in entries.items():
            value = row.get("packet")
            if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
                raise ValueError(f"Invalid declared assessment path: {name}/{label}")
            path = PurePosixPath(value)
            if not path.is_absolute() or path.as_posix() != value or ".." in path.parts or path.name != label:
                raise ValueError(f"Assessment path does not name its packet: {name}/{label}")
            if packet_root is None:
                packet_root = path.parent
            if path.parent != packet_root or packet_paths.get(label, value) != value:
                raise ValueError(f"Assessment packet paths disagree: {name}/{label}")
            packet_paths[label] = value
        raw = document(record["output_sha256"])
        if raw["assessment_id"] != name or "limitations" not in raw:
            raise ValueError(f"Invalid assessment output: {name}")
        assessments[name] = keyed(raw["runs"], "label")
        if set(assessments[name]) != set(labels):
            raise ValueError(f"Incomplete assessment: {name}")
        for label, row in assessments[name].items():
            if row["case_id"] != label_cases[label] or set(keyed(row["requirements"], "id")) != set(criteria[row["case_id"]]):
                raise ValueError(f"Assessment criteria or task changed: {name}/{label}")
            outcome(row["requirements"])
            if any(not isinstance(r.get("evidence"), str) or not r["evidence"].strip() for r in row["requirements"]):
                raise ValueError(f"Unsupported assessment judgment: {name}/{label}")
        inventory(record.get("retained_files", {}), blobs, name, allow_empty=True)
    if grades["assessment_summary"] != assessment_statistics(mapping, calibration, assessments):
        raise ValueError("Published assessment sensitivity or calibration differs")
    adjudications = {}
    for row in grades["adjudications"]:
        identity = (row["run_id"], row["criterion_id"])
        if identity in adjudications or row["run_id"] not in planned or row["criterion_id"] not in criteria[planned[row["run_id"]]["case_id"]]:
            raise ValueError("Duplicate or foreign adjudication")
        if not isinstance(row.get("rationale"), str) or not row["rationale"].strip():
            raise ValueError("Adjudication needs a contract-grounded rationale")
        adjudications[identity] = row
    inverse = {identity: label for label, identity in labels.items()}
    for run_id, final in keyed(grades["runs"], "run_id").items():
        label = inverse[run_id]
        originals = {name: keyed(rows[label]["requirements"], "id") for name, rows in assessments.items()}
        for criterion in final["requirements"]:
            initial = {name: rows[criterion["id"]]["status"] for name, rows in originals.items()}
            decision = adjudications.get((run_id, criterion["id"]))
            changed = len(set(initial.values())) != 1 or criterion["status"] not in initial.values()
            if changed and decision is None:
                raise ValueError(f"Unrecorded disagreement or changed consensus: {run_id}/{criterion['id']}")
            if decision is not None and (decision["initial_statuses"] != initial or decision["final_status"] != criterion["status"]):
                raise ValueError(f"Adjudication does not match its original/final grades: {run_id}/{criterion['id']}")
    return assessments


def load_verified():
    names = ("comparison-plan.json", "comparison-evidence.json", "comparison-grades.json", "comparison-rubric.json")
    plan, evidence, grades, rubric = map(read_json, names)
    if any(not isinstance(record, dict) for record in (plan, evidence, grades, rubric)):
        raise ValueError("Study records must be JSON objects")
    input_digests = plan.get("input_digests")
    if not isinstance(input_digests, dict) or not input_digests:
        raise ValueError("Frozen input digests must be a nonempty object")
    for name, expected in input_digests.items():
        safe_relative(name)
        if digest((HERE / name).read_bytes()) != expected:
            raise ValueError(f"Frozen study input changed: {name}")
    cases = read_json("comparison-cases.json")
    input_cases = keyed(cases["cases"], "id")
    if set(input_cases) != set(keyed(rubric["cases"], "id")):
        raise ValueError("Task inputs and rubric population differ")
    identities = [(names[0], evidence["plan_sha256"]),
                  (names[1], grades["evidence_sha256"]),
                  (names[3], grades["rubric_sha256"])]
    for name, expected in identities:
        if digest((HERE / name).read_bytes()) != expected:
            raise ValueError(f"Evidence/measurement identity changed: {name}")
    verify(plan, evidence, grades, rubric)
    verify_assessments(plan, evidence, grades, rubric, cases)
    verify_publication_files(evidence, grades)
    return plan, evidence, grades, rubric


def new_plain_directory(output):
    """Reject indirect ancestors before creating any part of a restore path."""
    output = Path(output).absolute()
    for node in (output, *output.parents):
        try:
            info = node.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or (
            getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise ValueError(f"Linked/reparse restore paths are not supported: {node}")
        if node == output:
            raise ValueError("Output path must be new; existing work is never overwritten")
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError(f"Restore ancestor is not a directory: {node}")
    output.mkdir(parents=True)
    return output


def materialize(run, blobs, output):
    inventory(run["output_files"], blobs, "restore", allow_empty=False)
    output = new_plain_directory(output)
    for name, sha in run["output_files"].items():
        path = output.joinpath(*safe_relative(name).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(blobs[sha].encode("utf-8"))
    return len(run["output_files"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    commands.add_parser("summary")
    restore = commands.add_parser("materialize")
    restore.add_argument("run")
    restore.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        data = load_verified()
        if args.command == "materialize":
            evidence = data[1]
            run = keyed(evidence["runs"], "run_id")[args.run]
            count = materialize(run, evidence["blobs"], args.output)
            print(f"Restored {args.run}: {count} files; no artifact executed")
        else:
            result = summarize(*data)
            if args.command == "check":
                if read_json("comparison-results.json") != result:
                    raise ValueError("Published results differ from the retained grades")
                print(f"comparison evidence: PASS ({result['assigned']} allocations; retained bytes, criteria and arithmetic)")
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))
    except (AttributeError, KeyError, OSError, ValueError, TypeError) as exc:
        print(f"comparison evidence: FAIL ({exc})")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
