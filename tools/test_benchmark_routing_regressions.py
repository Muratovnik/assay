"""Regressions for PR review findings; synthetic observations, never model calls."""
from __future__ import annotations

import copy
import unittest

from test_benchmark_router import candidate, cohort, data, request, row, view
from route_evidence.core import EvidenceError, validate_snapshot
from route_evidence.providers import SOURCES, captured_snapshot, heading_identity
from route_evidence.routing import brief, build_context, validate_request


def two_config_request(*task_types, **kwargs):
    return request(*task_types, available=[{"model": "frontier-a", "efforts": ["low"]},
                                           {"model": "economy-b", "efforts": ["max"]}], **kwargs)


def primary_pair(a=.8, b=.79, a_cost=1, b_cost=2):
    return view(rows=[row(score=a, cost=a_cost), row("economy-b", "max", b, b_cost)])


def frontier_pair(a=.8, b=.79, a_cost=1, b_cost=2, **kwargs):
    return view("frontiercode", [row(score=a, cost=a_cost, subset="extended"),
                                row("economy-b", "max", b, b_cost, subset="extended")], **kwargs)


def by_source(result, source_id, task=0, kind="primary_comparisons"):
    return next(c for c in result["tasks"][task][kind] if c["source_id"] == source_id)


class ReviewRegressionTests(unittest.TestCase):
    def test_missing_cost_does_not_hide_a_known_quality_failure(self):
        result = build_context(two_config_request(), [primary_pair(), frontier_pair(.3, .9, None, None)])
        failing = candidate(by_source(result, "frontiercode"), "frontier-a", "low")
        self.assertEqual(failing["quality_delta_pp"], 60.0)
        self.assertEqual(failing["expenses"], {})
        # An unpriced row may never be presented as undominated on a price axis.
        self.assertEqual(failing["frontier"], [])
        self.assertIn("unknown_primary_expense", result["tasks"][0]["evidence_gaps"])

    def test_known_primary_cost_violation_is_not_ignored(self):
        result = build_context(two_config_request(max_cost_usd=2), [primary_pair(), frontier_pair(a_cost=10, b_cost=15)])
        flags = [f for c in by_source(result, "frontiercode")["candidates"] for f in c["constraints"]]
        self.assertEqual({f["status"] for f in flags}, {"exceeds"})
        self.assertEqual(result["declared_constraints"], {"max_cost_usd": 2})

    def test_unknown_limit_is_reported_as_unknown_not_as_compliance(self):
        result = build_context(two_config_request(max_duration_seconds=100), [primary_pair(), frontier_pair()])
        statuses = {f["status"] for c in by_source(result, "deepswe")["candidates"] for f in c["constraints"]}
        self.assertEqual(statuses, {"unknown"})

    def test_a_cheaper_axis_cannot_hide_a_conflicting_primary_source(self):
        result = build_context(two_config_request(), [
            view(rows=[row(output_tokens=10), row("economy-b", "max", .79, 2, output_tokens=20)]),
            frontier_pair(.1, .9, None, None)])
        cheap = candidate(by_source(result, "deepswe"), "frontier-a", "low")
        conflicting = candidate(by_source(result, "frontiercode"), "frontier-a", "low")
        self.assertIn("output_tokens", cheap["frontier"])
        # Winning one axis in one cohort never edits the other cohort's evidence.
        self.assertEqual(conflicting["quality_delta_pp"], 80.0)

    def test_disjoint_primary_results_stay_separate(self):
        result = build_context(two_config_request(), [primary_pair(.9, .2), frontier_pair(.2, .9)])
        self.assertEqual(candidate(by_source(result, "deepswe"), "economy-b", "max")["quality_delta_pp"], 70.0)
        self.assertEqual(candidate(by_source(result, "frontiercode"), "frontier-a", "low")["quality_delta_pp"], 70.0)

    def test_coverage_is_not_union_of_primary_sources(self):
        result = build_context(two_config_request(), [view(), frontier_pair()])
        task = result["tasks"][0]
        self.assertIn({"model": "economy-b", "effort": "max"}, task["unmeasured"])
        first = next(c for c in task["coverage"] if c["source_id"] == "deepswe")
        self.assertFalse(first["comparative"])
        self.assertEqual(first["missing_candidates"], [{"model": "economy-b", "effort": "max"}])

    def test_support_cannot_close_missing_primary_coverage(self):
        support = view("cursorbench", [row(), row("economy-b", "max", .79, 2)])
        result = build_context(two_config_request(), [view(), support])
        task = result["tasks"][0]
        self.assertIn({"source_id": "frontiercode", "subset": "extended"}, task["missing_primary"])
        self.assertEqual(len(task["unmeasured"]), 2)
        self.assertEqual(by_source(result, "cursorbench", kind="supporting_comparisons")["source_id"], "cursorbench")

    def test_support_alone_is_no_primary_evidence(self):
        result = build_context(two_config_request(), [view("cursorbench", [row()])])
        task = result["tasks"][0]
        self.assertEqual(task["primary_comparisons"], [])
        self.assertTrue(task["supporting_comparisons"])
        self.assertEqual(len(task["missing_primary"]), 2)

    def test_complete_agreement_leaves_no_gaps(self):
        result = build_context(two_config_request(), [primary_pair(), frontier_pair()])
        self.assertEqual(result["tasks"][0]["evidence_gaps"], [])

    def test_complete_singleton_is_still_not_comparative(self):
        req = request("terminal", available=[{"model": "frontier-a", "efforts": ["low"]}])
        result = build_context(req, [view("terminal-bench")])
        self.assertIn("noncomparative_singleton", result["tasks"][0]["evidence_gaps"])

    def test_stale_quality_only_primary_still_reports_both_gaps(self):
        result = build_context(two_config_request(), [primary_pair(), frontier_pair(a_cost=None, b_cost=None, stale=True)])
        gaps = result["tasks"][0]["evidence_gaps"]
        self.assertIn("stale_primary_evidence", gaps)
        self.assertIn("unknown_primary_expense", gaps)

    def test_stale_negative_is_observed_unless_explicitly_excluded(self):
        evidence = [primary_pair(), frontier_pair(.1, .9, None, None, stale=True)]
        included = build_context(two_config_request(), evidence)
        self.assertEqual(candidate(by_source(included, "frontiercode"), "frontier-a", "low")["quality_delta_pp"], 80.0)
        excluded = build_context(two_config_request(allow_stale=False), evidence)
        self.assertEqual([c["source_id"] for c in excluded["tasks"][0]["primary_comparisons"]], ["deepswe"])
        self.assertIn("missing_primary_source_or_subset", excluded["tasks"][0]["evidence_gaps"])

    def test_quality_only_candidates_keep_scores_and_provenance(self):
        result = build_context(two_config_request("investigation"),
                               [view("swe-atlas-qna", [row(cost=None), row("economy-b", "max", .79, None)])])
        candidates = by_source(result, "swe-atlas-qna")["candidates"]
        self.assertEqual(len(candidates), 2)
        self.assertTrue(all(c["expense_evidence"] == "none" for c in candidates))
        self.assertTrue(all(c["source_url"] for c in candidates))

    def test_multiple_alias_rows_are_not_counted_as_independent_configurations(self):
        req = two_config_request()
        req["available"][0]["evidence_names"] = ["a-alias"]
        with self.assertRaises(EvidenceError):
            build_context(req, [view(rows=[row(), row("a-alias")])])

    def test_duplicate_source_envelope_is_rejected(self):
        with self.assertRaises(EvidenceError):
            build_context(two_config_request(), [view(), view()])

    def test_brief_never_truncates_gaps_or_candidates(self):
        result = build_context(request(), [view()])
        summary = brief(result)
        self.assertEqual(summary["tasks"][0]["unmeasured"], result["tasks"][0]["unmeasured"])
        self.assertEqual(len(summary["tasks"][0]["unmeasured"]), 3)
        self.assertEqual(cohort(summary)["missing_candidates"], cohort(result)["missing_candidates"])

    def test_inputs_are_not_mutated(self):
        snapshot = data()
        before = copy.deepcopy(snapshot)
        validate_snapshot(snapshot)
        self.assertEqual(before, snapshot)

    def test_malformed_or_unbounded_request_values(self):
        for change in ({"task_types": "implementation"}, {"task_types": []}, {"task_types": [" implementation "]},
                       {"quality_loss_pp": True}, {"quality_loss_pp": float("inf")}, {"min_score": 2}):
            with self.subTest(change=str(change)[:100]), self.assertRaises(EvidenceError):
                validate_request(request(**change))


class CaptureProofTests(unittest.TestCase):
    def test_historical_version_mention_is_not_active_identity(self):
        with self.assertRaises(EvidenceError):
            heading_identity(SOURCES["terminal-bench"], "Terminal-Bench 5.0; history: Terminal-Bench 4.0")

    def test_frontier_generic_title_requires_selected_version(self):
        source = SOURCES["frontiercode"]
        with self.assertRaises(EvidenceError):
            heading_identity(source, "FrontierCode Leaderboard")
        heading_identity(source, "FrontierCode Leaderboard", selected_version="FrontierCode 1.1")
        with self.assertRaises(EvidenceError):
            heading_identity(source, "FrontierCode Leaderboard", selected_version="FrontierCode 1.0")

    def test_parent_rejects_missing_or_wrong_subset_proof(self):
        proof = {"heading": "FrontierCode Leaderboard", "selected_version": "FrontierCode 1.1"}
        table = [["Model", "Score", "Cost"], ["Example low", "70%", "$1"]]
        capture = {"identity": proof, "parts": [
            {"subset": s, "observed_subset": s, "identity": proof, "tables": [table]}
            for s in ("main", "extended")]}
        result = captured_snapshot(SOURCES["frontiercode"], capture)
        self.assertEqual({r["subset"] for r in result["rows"]}, {"main", "extended"})
        capture["parts"][1]["observed_subset"] = "main"
        with self.assertRaises(EvidenceError):
            captured_snapshot(SOURCES["frontiercode"], capture)

    def test_parent_rejects_duplicate_parts_even_if_set_matches(self):
        proof = {"heading": "Terminal-Bench 4.0", "selected_version": None}
        part = {"subset": "all", "observed_subset": "all", "identity": proof,
                "tables": [[["Model", "Score"], ["Example low", "70%"]]]}
        with self.assertRaises(EvidenceError):
            captured_snapshot(SOURCES["terminal-bench"], {"identity": proof, "parts": [part, part]})

    def test_parent_rejects_revision_drift(self):
        capture = {"identity": {"heading": "Terminal-Bench 5.0", "selected_version": None}, "parts": []}
        with self.assertRaises(EvidenceError):
            captured_snapshot(SOURCES["terminal-bench"], capture)


if __name__ == "__main__":
    unittest.main()
