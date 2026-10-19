"""Consumer regressions for cost units, quality intervals and quoted guidance."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "route-subagents" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from route_evidence.core import EvidenceError
from route_evidence.guides import GUIDES, guide_snapshot
from route_evidence.providers import SOURCES, captured_snapshot, parse_tables, snapshot as measured_snapshot
from route_evidence.routing import build_context

AVAILABLE = [{"model": "economy", "efforts": ["low"]}, {"model": "capable", "efforts": ["high"]}]


class MeasurementBoundaryTests(unittest.TestCase):
    def test_terminal_browser_keeps_run_totals_outside_comparable_expenses(self):
        proof = {"heading": "Terminal-Bench", "selected_version": "Terminal-Bench 4.0"}
        table = [["Model", "Agent", "Resolution Rate", "Tokens", "Cost"],
                 ["economy (low)", "Codex", "81% ± 5%", "1k", "$100"],
                 ["capable (high)", "Codex", "80% ± 5%", "2k", "$200"]]
        data = captured_snapshot(SOURCES["terminal-bench"], {"identity": proof, "parts": [
            {"subset": "all", "observed_subset": "all", "identity": proof, "tables": [table]}]})
        self.assertEqual(data["rows"][0]["aggregate_usage"], {"total_cost_usd": 100, "total_tokens": 1000})
        request = {"client": "codex", "task_types": ["terminal"], "max_cost_usd": 150,
                   "available": AVAILABLE}
        result = build_context(request, [{"source_id": "terminal-bench", "snapshot": data, "stale": False}])
        candidates = result["tasks"][0]["primary_comparisons"][0]["candidates"]
        for candidate in candidates:
            self.assertEqual(candidate["expenses"], {})
            self.assertEqual(candidate["dominated_by"], [])
            self.assertEqual(candidate["constraints"][0]["status"], "unknown")
        self.assertAlmostEqual(candidates[0]["score_low"], .76)
        self.assertAlmostEqual(candidates[0]["score_high"], .86)

    def test_published_overlap_is_not_lost_before_pareto_comparison(self):
        source = SOURCES["cursorbench"]
        table = [["Model", "Score", "Cost / Task", "Tokens / Task", "Steps / Task"],
                 ["economy (low)", "81% ± 5%", "$1", "100", "1"],
                 ["capable (high)", "80% ± 5%", "$2", "200", "2"]]
        data = measured_snapshot(source, parse_tables(source, [table]))
        request = {"client": "codex", "task_types": ["implementation"],
                   "available": AVAILABLE}
        result = build_context(request, [{"source_id": source["id"], "snapshot": data, "stale": False}])
        candidates = result["tasks"][0]["supporting_comparisons"][0]["candidates"]
        self.assertEqual([c["dominated_by"] for c in candidates], [[], []])
        self.assertEqual([c["measured_below"] for c in candidates], [[], []])
        self.assertEqual(candidates[0]["expenses"]["cost_usd"], 1)
        table[1][1] = "81% ± invalid"
        with self.assertRaises(EvidenceError):
            measured_snapshot(source, parse_tables(source, [table]))


class QualityIntervalTests(unittest.TestCase):
    def candidates(self, rows):
        source = SOURCES["cursorbench"]
        table = [["Model", "Score", "Cost / Task", "Tokens / Task", "Steps / Task"], *[[*row, "100", "1"] for row in rows]]
        request = {"client": "codex", "task_types": ["implementation"],
                   "available": AVAILABLE}
        data = measured_snapshot(source, parse_tables(source, [table]))
        result = build_context(request, [{"source_id": source["id"], "snapshot": data, "stale": False}])
        return {c["model"]: c for c in result["tasks"][0]["supporting_comparisons"][0]["candidates"]}

    def test_only_a_wholly_higher_published_interval_marks_a_route_measured_below(self):
        separated = self.candidates([["economy (low)", "60% ± 5%", "$1"], ["capable (high)", "80% ± 5%", "$2"]])
        self.assertEqual(separated["economy"]["measured_below"], [{"model": "capable", "effort": "high"}])
        self.assertEqual(separated["capable"]["measured_below"], [])
        overlapping = self.candidates([["economy (low)", "72% ± 5%", "$1"], ["capable (high)", "80% ± 5%", "$2"]])
        self.assertEqual(overlapping["economy"]["measured_below"], [])
        point_only = self.candidates([["economy (low)", "40%", "$1"], ["capable (high)", "80%", "$2"]])
        self.assertEqual(point_only["economy"]["measured_below"], [])


class GuidanceBoundaryTests(unittest.TestCase):
    def guide(self, content):
        source = GUIDES["openai-reasoning"]
        first, second = source["sections"]
        return guide_snapshot(source, f"# Example\n\n## {first}\n\n{content}\n\n## {second}\n\nCosts.")

    def test_caveat_limits_fail_instead_of_publishing_incomplete_guidance(self):
        for content in ("\n\n".join(f"<Warning>condition {i}</Warning>" for i in range(7)),
                        "<Warning>" + "x" * 801 + " Do not use this setting.</Warning>"):
            with self.subTest(content=content[:60]), self.assertRaisesRegex(EvidenceError, "caveat"):
                self.guide(content)
        valid = self.guide("\n\n".join(f"<Warning>condition {i}</Warning>" for i in range(6)))
        self.assertEqual(len(valid["retrieved_sections"][0]["caveats"]), 6)

    def test_code_examples_do_not_become_vendor_caveats(self):
        for code in ("```xml\n<Warning>quoted example</Warning>\n```",
                     "````markdown\n```xml\n<Warning>quoted example</Warning>\n```\n````"):
            with self.subTest(code=code):
                section = self.guide(code + "\n\n<Note>Actual condition.</Note>")["retrieved_sections"][0]
                self.assertEqual(section["caveats"], [{"kind": "note", "text": "Actual condition.", "truncated": False}])
                self.assertEqual(section["code_blocks_omitted"], 1)


if __name__ == "__main__":
    unittest.main()
