"""Native categorical assessments over an exact routing snapshot."""
from __future__ import annotations

import copy

from .advice_contracts import _metadata_value, _object, _reason_codes, _safe_name, MAX_METADATA_BYTES
from .core import EvidenceError, encoded, effort, text

CHOICES = {"adequate", "inadequate", "unknown"}


def needs_assessment(packet):
    return len(packet["eligible"]) > 1 and set(packet["explicit"]) != {"model", "effort"}


def packet_cohort_ids(snapshot, packet, role=None):
    keys = (role + "_cohort_ids",) if role else ("primary_cohort_ids", "supporting_cohort_ids")
    return {ref for task in snapshot["evidence"]["tasks"] if task["task_type"] in packet["task_types"]
            for key in keys for ref in task[key]}


def question_bindings(snapshot):
    bindings = {}
    refs = {c["candidate_id"]: index for index, c in enumerate(snapshot["candidates"])}
    for index, packet in enumerate(snapshot["packets"]):
        if needs_assessment(packet):
            for candidate in packet["eligible"]:
                bindings[f"p{index}.c{refs[candidate]}"] = (packet["packet_id"], candidate)
    return bindings


def result_contract(snapshot, model, level, version):
    return {"schema_version": 2, "snapshot_id": snapshot["snapshot_id"], "backend": "native-economy",
            "requested_model": model, "resolved_model": model, "effort": level,
            "answers": [{"name": name, "choice": "unknown", "basis": "b0"} for name in question_bindings(snapshot)],
            "assessments": [{"packet_id": p["packet_id"], "bases": [{"id": "b0", "kind": "unknown",
                "criterion_ids": [], "cohort_ids": [], "explanation": "Replace with the missing facts or task-specific basis.",
                "unknowns": ["task_adequacy"]}]} for p in snapshot["packets"] if needs_assessment(p)],
            "probabilities": None, "confidence": None,
            "metadata": {"contract_version": version, "explanation_source": "native_task_adequacy"}}


def validate_decision_result(snapshot, result):
    required = {"schema_version", "snapshot_id", "backend", "requested_model", "resolved_model", "effort",
                "answers", "assessments", "probabilities", "confidence", "metadata"}
    result = _object(copy.deepcopy(result), "decision result", required, required)
    if snapshot["policy"]["schema_version"] != 3 or result["schema_version"] != 2:
        raise EvidenceError("native_decision_policy_mismatch")
    if result["snapshot_id"] != snapshot["snapshot_id"] or result["backend"] != "native-economy":
        raise EvidenceError("native_decision_snapshot_or_backend_mismatch")
    for key in ("requested_model", "resolved_model"):
        result[key] = text(result[key], "decision result." + key)
    result["effort"] = effort(result["effort"])
    if result["effort"] is None:
        raise EvidenceError("native_decision_explicit_effort_required")
    if result["probabilities"] is not None or result["confidence"] is not None:
        raise EvidenceError("native_numeric_confidence_forbidden")
    bindings = question_bindings(snapshot)
    packets = {p["packet_id"]: p for p in snapshot["packets"] if needs_assessment(p)}
    assessments = result["assessments"]
    if not isinstance(assessments, list) or len(assessments) != len(packets):
        raise EvidenceError("native_decision_assessments_required")
    bases, seen = {}, set()
    for assessment in assessments:
        assessment = _object(assessment, "assessment", {"packet_id", "bases"}, {"packet_id", "bases"})
        packet_id = assessment["packet_id"]
        if not isinstance(packet_id, str) or packet_id not in packets or packet_id in seen:
            raise EvidenceError("native_decision_assessment_packet_invalid")
        seen.add(packet_id)
        packet = packets[packet_id]
        if "task_spec" not in packet:
            raise EvidenceError("native_task_details_required")
        criteria = {c["id"] for c in packet["task_spec"]["criteria"]}
        cohorts = packet_cohort_ids(snapshot, packet)
        entries = assessment["bases"]
        if not isinstance(entries, list) or not 1 <= len(entries) <= len(packet["eligible"]):
            raise EvidenceError("native_decision_bases_invalid")
        for basis in entries:
            fields = {"id", "kind", "criterion_ids", "cohort_ids", "explanation", "unknowns"}
            basis = _object(basis, "basis", fields, fields)
            basis_id = _safe_name(basis["id"], "basis.id")
            if len(basis_id) > 16 or (packet_id, basis_id) in bases:
                raise EvidenceError("native_decision_basis_id_invalid")
            if not isinstance(basis["kind"], str) or basis["kind"] not in {"measurement", "task_inference", "unknown"}:
                raise EvidenceError("native_decision_basis_kind_invalid")
            for key, allowed in (("criterion_ids", criteria), ("cohort_ids", cohorts)):
                refs = basis[key]
                if (not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs)
                        or len(set(refs)) != len(refs) or not set(refs) <= allowed):
                    raise EvidenceError("native_decision_" + key + "_invalid")
            explanation = basis["explanation"]
            if (not isinstance(explanation, str) or not explanation.strip() or len(explanation) > 300
                    or any(ord(c) < 32 for c in explanation) or explanation.startswith("Replace with")):
                raise EvidenceError("native_decision_explanation_invalid")
            basis["unknowns"] = _reason_codes(basis["unknowns"], "basis.unknowns")
            bases[packet_id, basis_id] = basis
    answers = result["answers"]
    if not isinstance(answers, list) or len(answers) != len(bindings):
        raise EvidenceError("native_decision_answers_required")
    seen = set()
    for answer in answers:
        answer = _object(answer, "answer", {"name", "choice", "basis"}, {"name", "choice", "basis"})
        name = answer["name"]
        if not isinstance(name, str) or name not in bindings or name in seen:
            raise EvidenceError("native_decision_question_invalid")
        seen.add(name)
        choice = answer["choice"]
        if not isinstance(choice, str) or choice not in CHOICES:
            raise EvidenceError("native_decision_choice_invalid")
        packet_id, candidate_id = bindings[name]
        basis_id = answer["basis"]
        if not isinstance(basis_id, str) or (packet_id, basis_id) not in bases:
            raise EvidenceError("native_decision_answer_basis_invalid")
        basis = bases[packet_id, basis_id]
        if choice == "unknown":
            if not basis["unknowns"] or basis["kind"] != "unknown":
                raise EvidenceError("native_decision_unknown_basis_required")
        elif not basis["criterion_ids"] or basis["kind"] == "unknown":
            raise EvidenceError("native_decision_task_criterion_required")
        if choice == "adequate" and set(basis["criterion_ids"]) != {c["id"] for c in packets[packet_id]["task_spec"]["criteria"]}:
            raise EvidenceError("native_decision_all_task_criteria_required")
        if choice != "unknown" and basis["kind"] == "measurement":
            from .advice_contracts import _compact_candidate
            ref = next(i for i, c in enumerate(snapshot["candidates"]) if c["candidate_id"] == candidate_id)
            measured = {c["cohort_id"] for c in snapshot["evidence"]["cohorts"]
                        if (_compact_candidate(c, ref) or {}).get("score") is not None}
            if not measured.intersection(basis["cohort_ids"]):
                raise EvidenceError("native_decision_exact_measurement_required")
    result["metadata"] = _metadata_value(result["metadata"], "metadata")
    if not isinstance(result["metadata"], dict) or len(encoded(result["metadata"])) > MAX_METADATA_BYTES:
        raise EvidenceError("native_decision_metadata_invalid")
    if len(encoded(result)) > snapshot["policy"]["max_advisor_result_bytes"]:
        raise EvidenceError("advisor_result_limit_exceeded")
    return result


def remap_packets(result, packet_map):
    for assessment in result["assessments"]:
        assessment["packet_id"] = packet_map[assessment["packet_id"]]
    # Question names use packet positions and candidate positions, which are
    # invariant under the semantic cache's packet-ID-only rebinding.
    return result
