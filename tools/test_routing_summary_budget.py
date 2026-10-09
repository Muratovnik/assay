"""Preserve useful task evidence within the existing advisor context budget."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_routing_decisions as decisions
from route_evidence.advice import decide
from route_evidence.advisors.native import parse_native
from route_evidence.core import EvidenceError, encoded
from route_evidence.task_costs import CATEGORIES, compare, estimates
from route_evidence.task_evidence import TaskEvidence, attach_summary, validate_summary


class TaskSummaryBudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = TaskEvidence(Path(self.tmp.name), {"enabled": True, "auto_download": False})

    def scenario(self, count, *, partial=False):
        packets = decisions.packets()
        packets[0].update(baseline={"model": "model-00", "effort": "low"},
                          cost_objective={"unit": "api_usd", "unit_basis": "tariff-v1", "overhead": .01})
        context = decisions.context(tuple(float(count - i) for i in range(count)), (1,) * count, count)
        snapshot = decisions.snapshot(ctx=context, task_packets=packets)
        rows = [{"task_id": "paired-task-" + str(task), "model": candidate["model"], "effort": candidate["effort"],
                 "metric": "accepted", "score": 1, "comparison_basis": "6" * 64,
                 "cost_scope": "chain", "costs": {"api_usd": float(index + 1)},
                 "unit_basis": {"api_usd": "tariff-v1"}, "complete": True,
                 "components": {category: {"api_usd": (index + 1) / 4} for category in CATEGORIES}}
                for task in range(3) for index, candidate in enumerate(snapshot["candidates"])]
        if partial:
            rows.append({**copy.deepcopy(rows[0]), "task_id": "unfinished-task", "complete": False, "score": None})
        return snapshot, rows

    def summarize(self, snapshot, rows, *, full=False, query=None):
        with patch.object(self.store, "local_rows", return_value=rows):
            queries = {"work-0": query} if query else None
            if full:
                with patch("route_evidence.task_evidence.MAX_SUMMARY", 100000):
                    return self.store.summarize(snapshot["packets"], snapshot["candidates"], queries)
            return self.store.summarize(snapshot["packets"], snapshot["candidates"], queries)

    def assert_only_component_detail_omitted(self, full, summary):
        expected = copy.deepcopy(full)
        for packet in expected["packets"]:
            for layer in ("public", "local"):
                for route in packet[layer]:
                    for group in route["groups"]:
                        group.pop("cost_components", None)
        expected["cost_detail"] = "totals_only"
        self.assertEqual(summary, expected)
        self.assertLessEqual(len(encoded(summary)), 6144)
        validate_summary(summary)

    def test_four_route_overflow_preserves_complete_comparisons_and_adequacy_selection(self):
        snapshot, rows = self.scenario(4, partial=True)
        full = self.summarize(snapshot, rows, full=True)
        self.assertGreater(len(encoded(full)), 6144)
        summary = self.summarize(snapshot, rows)
        self.assertEqual(summary["status"], "available")
        self.assert_only_component_detail_omitted(full, summary)
        packet = summary["packets"][0]
        self.assertEqual(len(packet["local"]), 4)
        self.assertEqual(len(packet["comparison"]["pairwise_comparisons"]), 6)
        self.assertEqual({pair["n"] for pair in packet["comparison"]["pairwise_comparisons"]}, {3})
        self.assertEqual(packet["local"][0]["groups"][0]["partial"], 1)
        self.assertEqual(packet["local"][0]["groups"][0]["unknown_quality"], 1)
        self.assertEqual(packet["local"][0]["groups"][0]["expected_cost"]["api_usd"]["mean"], 1)
        measured = attach_summary(snapshot, summary)
        selected = decide(measured, parse_native(measured, decisions.answer(measured)))[0]
        self.assertEqual(selected["selected"]["model"], "model-00")
        self.assertIn("paired_chain_cost_selected", selected["reason_codes"])
        baseline = decide(snapshot, parse_native(snapshot, decisions.answer(snapshot)))[0]
        self.assertEqual(baseline["selected"]["model"], "model-03")
        inadequate = decide(measured, parse_native(measured, decisions.answer(measured, {"model-00": "inadequate"})))[0]
        self.assertEqual(inadequate["selected"]["model"], "model-01")
        self.assertEqual(set(estimates(rows, snapshot["candidates"])[0]["groups"][0]["cost_components"]), CATEGORIES)
        raw = compare(rows, snapshot["candidates"], snapshot["candidates"][0]["candidate_id"], "api_usd", .01)
        self.assertEqual(len(raw["comparisons"]), 3)
        self.assertEqual(len(raw["pairwise_comparisons"]), 6)

    def test_two_and_three_route_summaries_retain_their_full_component_detail(self):
        for count in (2, 3):
            with self.subTest(count=count):
                snapshot, rows = self.scenario(count)
                summary = self.summarize(snapshot, rows)
                self.assertEqual(summary, self.summarize(snapshot, rows, full=True))
                self.assertEqual(summary["status"], "available")
                self.assertNotIn("cost_detail", summary)
                for index, route in enumerate(summary["packets"][0]["local"]):
                    components = route["groups"][0]["cost_components"]
                    self.assertEqual(set(components), CATEGORIES)
                    self.assertEqual({cost["api_usd"]["mean"] for cost in components.values()}, {(index + 1) / 4})

    def test_compaction_preserves_public_local_separation_and_unknown_routes(self):
        snapshot, rows = self.scenario(3)
        query = "repair decimal parser"
        self.store.install({"schema_version": 1,
            "source": {"id": "public-fixture", "revision": "r1", "url": "https://example.invalid/data",
                       "license": "fixture-only", "use": "local-only"},
            "records": [{"task_id": "public-case", "task_types": ["implementation"], "features": {}, "query": query,
                "observations": [{"model": "model-00", "effort": "low", "metric": "pass_at_1",
                    "comparison_basis": "public-response", "score": 0, "cost_scope": "response", "complete": True,
                    "costs": {"api_usd": .01}, "unit_basis": {"api_usd": "public-tariff"}}]}]})
        full = self.summarize(snapshot, rows, full=True, query=query)
        self.assertGreater(len(encoded(full)), 6144)
        summary = self.summarize(snapshot, rows, query=query)
        self.assert_only_component_detail_omitted(full, summary)
        packet = summary["packets"][0]
        self.assertEqual(packet["public"][0]["groups"][0]["quality"]["mean"], 0)
        self.assertEqual(packet["local"][0]["groups"][0]["quality"]["mean"], 1)
        self.assertEqual(packet["unknown_current_candidates"]["public"],
                         [candidate["candidate_id"] for candidate in snapshot["candidates"][1:]])

    def test_still_oversized_summary_omits_every_packet_and_rejects_unknown_detail_labels(self):
        snapshot, rows = self.scenario(6)
        summary = self.summarize(snapshot, rows)
        self.assertEqual(summary["status"], "insufficient_coverage")
        self.assertEqual(summary["reason"], "summary_budget_exceeded")
        self.assertEqual(summary["packets"], [])
        for value in ("response_only", [], None):
            with self.subTest(cost_detail=value), self.assertRaises(EvidenceError):
                validate_summary({**summary, "cost_detail": value})


if __name__ == "__main__":
    unittest.main()
