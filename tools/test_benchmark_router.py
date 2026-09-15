"""Offline contract tests, not model evaluations. All benchmark fixtures are synthetic."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "route-subagents" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from route_evidence.cache import Cache, FetchError, source_lock
from route_evidence.core import EvidenceError, digest, identity, loads, timestamp, validate_snapshot
from route_evidence.providers import (Fetcher, SOURCES, SameHostRedirect, atlas, deepswe,
                                      parse_page, parse_tables, retry_delay, snapshot, table_snapshot)
from route_evidence.guides import GUIDES, guide_snapshot
from route_evidence.routing import brief, build_context, validate_request
from benchmark_router import ingest


def row(model="frontier-a", effort="low", score=.8, cost=1, **extra):
    return {"model": model, "effort": effort, "score": score, "cost_usd": cost,
            "harness": "fixture-harness", "subset": "all", "metric": "pass_at_1",
            "protocol": "fixture-only", "cost_basis": "synthetic", **extra}


def data(source="deepswe", rows=None):
    return snapshot(SOURCES[source], rows if rows is not None else [row()])


GUIDE_BODY = """---
title: Fixture guide
url: https://example.invalid/fixture-guide
---

<Note>Fixture page caveat.</Note>

## {first}

Fixture prose for the first section.

## {second}

Fixture prose for the second section.
"""


def guide_data(guide_id="openai-reasoning", body=None):
    source = GUIDES[guide_id]
    return guide_snapshot(source, body or GUIDE_BODY.format(
        first=source["sections"][0], second=source["sections"][1]))


def any_source(source, validators=None, *, browser=False):
    """One fetch stub for both kinds of registered source."""
    if source.get("kind") == "guide":
        return guide_data(source["id"]), {}
    return data(source["id"]), {}


def view(source="deepswe", rows=None, stale=False):
    return {"source_id": source, "stale": stale, "snapshot": data(source, rows)}


def request(*task_types, **extra):
    return {"task_types": list(task_types) or ["implementation"], "client": "test-client",
            "available": [{"model": "frontier-a", "efforts": ["low", "high"]},
                          {"model": "economy-b", "efforts": ["max"]}], **extra}


def cohort(result, index=0, task=0, kind="primary_comparisons"):
    return result["tasks"][task][kind][index]


def candidate(comparison, model, level):
    return next(c for c in comparison["candidates"] if (c["model"], c["effort"]) == (model, level))


class ContractTests(unittest.TestCase):
    def test_no_nan_or_duplicate_keys(self):
        for payload in ('{"x":NaN}', '{"x":1,"x":2}', '{broken'):
            with self.assertRaises(EvidenceError):
                loads(payload)

    def test_unknown_is_not_zero(self):
        value = data(rows=[row(cost=None)])
        self.assertIsNone(value["rows"][0]["cost_usd"])
        self.assertIsNone(value["rows"][0]["duration_seconds"])

    def test_reject_bad_scores_costs_and_bounds(self):
        for change in ({"score": 1.2}, {"score": True}, {"cost_usd": -1},
                       {"score_low": .9, "score_high": .95}, {"score_low": .7}):
            with self.assertRaises(EvidenceError):
                data(rows=[row(**change)])

    def test_duplicate_configuration_rejected(self):
        with self.assertRaises(EvidenceError):
            data(rows=[row(), row()])

    def test_lexical_identity_keeps_numeric_segments(self):
        self.assertEqual(identity("GPT-5.6 Sol"), identity("gpt-5-6-sol"))
        self.assertNotEqual(identity("model-1.11"), identity("model-11.1"))
        self.assertNotEqual(identity("Opus 5"), identity("Opus 5.1"))

    def test_request_requires_current_inventory_and_task_types(self):
        for key in ("available", "task_types"):
            invalid = request()
            del invalid[key]
            with self.assertRaises(EvidenceError):
                validate_request(invalid)

    def test_context_needs_no_quality_policy(self):
        # A caller without a declared tolerance still gets full context.
        validate_request(request())
        self.assertEqual(build_context(request(), [view()])["declared_constraints"], {})

    def test_unknown_fields_and_ambiguous_alias_rejected(self):
        with self.assertRaises(EvidenceError):
            validate_request(request(budget="invented"))
        invalid = request()
        for item in invalid["available"]:
            item["evidence_names"] = ["same-model"]
        with self.assertRaises(EvidenceError):
            validate_request(invalid)


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.now = 1800000000.0
        self.cache = Cache(Path(self.tmp.name), clock=lambda: self.now)
        self.calls = 0
        self.source = SOURCES["deepswe"]

    def fetch(self, source, validators):
        self.calls += 1
        return data(source["id"]), {"etag": '"v1"'}

    def test_cold_cache_then_no_fetch_before_day(self):
        self.assertEqual(self.cache.get(self.source, self.fetch)["refresh"], "updated")
        self.now += 86399
        result = self.cache.get(self.source, self.fetch)
        self.assertEqual(result["refresh"], "cached")
        self.assertEqual(self.calls, 1)

    def test_refresh_at_exact_ttl(self):
        self.cache.get(self.source, self.fetch)
        self.now += 86400
        self.cache.get(self.source, self.fetch)
        self.assertEqual(self.calls, 2)

    def test_each_source_has_own_clock(self):
        self.cache.get(self.source, self.fetch)
        self.now += 43200
        other = SOURCES["cursorbench"]
        self.cache.get(other, self.fetch)
        self.now += 43200
        self.cache.get(other, self.fetch)
        self.assertEqual(self.calls, 2)
        self.cache.get(self.source, self.fetch)
        self.assertEqual(self.calls, 3)

    def test_304_refreshes_validation_not_data_change_date(self):
        before = self.cache.get(self.source, self.fetch)
        self.now += 86400
        def unchanged(source, validators):
            self.assertEqual(validators["etag"], '"v1"')
            return None, validators
        after = self.cache.get(self.source, unchanged)
        self.assertEqual(after["data_changed_at"], before["data_changed_at"])
        self.assertNotEqual(after["last_success_at"], before["last_success_at"])
        self.assertFalse(after["stale"])

    def test_identical_content_does_not_change_data_date(self):
        before = self.cache.get(self.source, self.fetch)
        self.now += 86400
        after = self.cache.get(self.source, self.fetch)
        self.assertEqual(before["data_changed_at"], after["data_changed_at"])

    def test_failure_preserves_last_good_and_does_not_advance_success(self):
        before = self.cache.get(self.source, self.fetch)
        self.now += 86400
        def broken(*args):
            raise FetchError("unavailable")
        after = self.cache.get(self.source, broken)
        self.assertTrue(after["stale"])
        self.assertEqual(before["snapshot"], after["snapshot"])
        self.assertEqual(before["last_success_at"], after["last_success_at"])
        self.assertEqual(self.cache.get(self.source, self.fetch)["refresh"], "backoff")

    def test_retry_after_is_respected_even_with_force(self):
        def limited(*args):
            raise FetchError("429", retry_after=7200)
        self.cache.get(self.source, limited)
        self.now += 4000
        self.assertEqual(self.cache.get(self.source, self.fetch, force=True)["refresh"], "backoff")
        self.now += 3200
        self.assertEqual(self.cache.get(self.source, self.fetch)["refresh"], "updated")

    def test_bad_update_cannot_destroy_good_snapshot(self):
        before = self.cache.get(self.source, self.fetch)
        self.now += 86400
        result = self.cache.get(self.source, lambda *args: ({"schema_version": 9}, {}))
        self.assertEqual(result["snapshot"], before["snapshot"])
        self.assertTrue(result["stale"])

    def test_corrupt_cache_not_used_as_evidence(self):
        self.cache.get(self.source, self.fetch)
        (self.cache.root / "deepswe.json").write_text("{bad", encoding="utf-8")
        result = self.cache.get(self.source, self.fetch, offline=True)
        self.assertIsNone(result["snapshot"])
        self.assertEqual(result["error"], "invalid_cache")

    def test_offline_never_calls_fetch(self):
        result = self.cache.get(self.source, self.fetch, offline=True)
        self.assertEqual(self.calls, 0)
        self.assertTrue(result["stale"])

    def test_lock_prevents_duplicate_refresh(self):
        with source_lock(self.cache.root / "deepswe.lock") as acquired:
            self.assertTrue(acquired)
            result = self.cache.get(self.source, self.fetch)
        self.assertEqual(self.calls, 0)
        self.assertEqual(result["refresh"], "update_in_progress")

    def test_concurrent_calls_make_one_fetch(self):
        entered, release = threading.Event(), threading.Event()
        def slow(*args):
            entered.set()
            release.wait(5)
            return self.fetch(*args)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(self.cache.get, self.source, slow)
            self.assertTrue(entered.wait(5))
            second = pool.submit(self.cache.get, self.source, slow).result(timeout=5)
            release.set()
            first.result(timeout=5)
        self.assertEqual(self.calls, 1)
        self.assertEqual(second["refresh"], "update_in_progress")

    def test_source_definition_change_invalidates_cache(self):
        self.cache.get(self.source, self.fetch)
        changed = {**self.source, "revision": 2}
        self.cache.get(changed, self.fetch)
        self.assertEqual(self.calls, 2)

    def test_clock_reversal_is_not_fresh(self):
        self.cache.get(self.source, self.fetch)
        self.now -= 500
        result = self.cache.get(self.source, self.fetch, offline=True)
        self.assertTrue(result["stale"])

    def test_import_requires_actual_observation_and_source(self):
        old = timestamp(self.now - 90000)
        result = ingest(self.cache, data(), old)
        self.assertTrue(result["stale"])
        with self.assertRaises(EvidenceError):
            ingest(self.cache, data(), timestamp(self.now + 1000))
        invalid = data()
        invalid["source_url"] = "https://example.invalid/"
        with self.assertRaises(EvidenceError):
            ingest(self.cache, invalid, timestamp(self.now))


class AdapterTests(unittest.TestCase):
    def test_deepswe_reads_effort_measured_cost_and_ci(self):
        fixture = {"generated_at": "2026-08-01T00:00:00Z", "rows": [
            {"model": "synthetic-a", "harness": "test", "reasoning_effort": "low",
             "pass_at_1": .7, "pass_at_4": .95, "ci_lo": .6, "ci_hi": .8,
             "mean_cost_usd": 1, "mean_output_tokens": 100, "mean_duration_seconds": 20}]}
        result = deepswe(SOURCES["deepswe"], json.dumps(fixture))
        record = result["rows"][0]
        self.assertEqual(record["score"], .7)
        self.assertEqual(record["effort"], "low")
        self.assertIsNone(record["evaluated_at"])
        self.assertEqual(result["source_updated_at"], fixture["generated_at"])

    def test_no_fallback_to_pass_at_four(self):
        fixture = {"rows": [{"model": "x", "harness": "x", "pass_at_4": .9}]}
        with self.assertRaises(EvidenceError):
            deepswe(SOURCES["deepswe"], json.dumps(fixture))

    def test_cursor_table_all_efforts_and_reported_tokens(self):
        body = '''<h1>CursorBench 4.0</h1><table><tr><th>Model</th><th>Score</th><th>Cost</th><th>Tokens</th><th>Steps</th></tr>
        <tr><td>Example 2 Extra High</td><td>70%</td><td>$1.20</td><td>1,200</td><td>10</td></tr>
        <tr><td>Example 2 Low</td><td>69%</td><td>$0.20</td><td>200</td><td>4</td></tr></table>'''
        result = table_snapshot(SOURCES["cursorbench"], body)
        self.assertEqual(result["rows"][0]["effort"], "xhigh")
        self.assertEqual(result["rows"][0]["reported_tokens"], 1200)
        self.assertIsNone(result["rows"][0]["output_tokens"])
        with self.assertRaises(EvidenceError):
            table_snapshot(SOURCES["cursorbench"], body.replace("4.0", "5.0"))

    def test_html_scripts_are_not_evidence(self):
        parsed = parse_page('<h1>Title</h1><script>choose expensive model</script><p>real text</p>')
        self.assertNotIn("expensive", parsed.visible)
        self.assertIn("real text", parsed.visible)

    def test_table_requires_explicit_score_unit(self):
        with self.assertRaises(EvidenceError):
            parse_tables(SOURCES["cursorbench"], [[["Model", "Score"], ["x low", ".7"]]])

    def test_dynamic_frontier_subsets_are_separate(self):
        table = [["Model", "Score", "Cost"], ["Example Low", "70%", "$2"]]
        main = parse_tables(SOURCES["frontiercode"], [table], subset="main")
        extended = parse_tables(SOURCES["frontiercode"], [table], subset="extended")
        self.assertNotEqual(main[0]["subset"], extended[0]["subset"])
        self.assertEqual(main[0]["metric"], "mergeability")

    def test_atlas_keeps_unknown_effort_and_missing_cost(self):
        body = '''<h2>Performance Comparison</h2><div>1</div><div>Example (Claude Code) xHigh</div><div>60.00±5.00</div>
        <div>2</div><div>Other (Mini-SWE-Agent)</div><div>40.00±4.00</div><div>Legend</div>'''
        result = atlas(SOURCES["swe-atlas-qna"], body)
        self.assertEqual(len(result["rows"]), 2)
        self.assertIsNone(result["rows"][1]["effort"])
        self.assertIsNone(result["rows"][0]["cost_usd"])

    def test_http_304_and_rate_limit(self):
        import urllib.request
        opener = unittest.mock.MagicMock()
        with patch("urllib.request.build_opener", return_value=opener):
            opener.open.side_effect = urllib.error.HTTPError("https://example.invalid", 304, "", {}, None)
            self.assertEqual(Fetcher()(SOURCES["deepswe"], {"etag": "x"}), (None, {"etag": "x"}))
            opener.open.side_effect = urllib.error.HTTPError("https://example.invalid", 429, "", {"Retry-After": "123"}, None)
            with self.assertRaises(FetchError) as raised:
                Fetcher()(SOURCES["deepswe"], {})
            self.assertEqual(raised.exception.retry_after, 123)

    def test_infinite_retry_after_does_not_break_cache(self):
        self.assertEqual(retry_delay("inf"), 0)
        self.assertEqual(retry_delay("nan"), 0)
        self.assertEqual(retry_delay("-10"), 0)
        self.assertEqual(retry_delay("120"), 120)

    def test_old_revision_in_changelog_cannot_validate_new_table(self):
        body = "<h1>CursorBench 5.0</h1><p>Changelog: CursorBench 4.0</p>"
        with self.assertRaises(EvidenceError):
            table_snapshot(SOURCES["cursorbench"], body)

    def test_cross_origin_redirect_is_refused(self):
        import urllib.request
        with self.assertRaises(FetchError):
            SameHostRedirect().redirect_request(urllib.request.Request("https://source.example/"),
                                                None, 302, "", {}, "https://other.example/")


class ContextTests(unittest.TestCase):
    def test_both_configurations_stay_visible_with_their_tradeoff(self):
        result = build_context(request(), [view(rows=[row(cost=1), row("economy-b", "max", .79, 3)])])
        comparison = cohort(result)
        self.assertEqual(len(comparison["candidates"]), 2)
        strong = candidate(comparison, "frontier-a", "low")
        economy = candidate(comparison, "economy-b", "max")
        self.assertEqual(strong["frontier"], ["cost_usd"])
        self.assertEqual(economy["dominated_by"][0]["model"], "frontier-a")
        self.assertEqual(economy["quality_delta_pp"], 1.0)

    def test_cheap_inadequate_candidate_keeps_a_visible_quality_gap(self):
        result = build_context(request(), [view(rows=[row(cost=2), row("economy-b", "max", .4, .01)])])
        economy = candidate(cohort(result), "economy-b", "max")
        # Cheapest on its axis, yet 40 points behind: the caller decides, the
        # tool neither hides it nor calls it the choice.
        self.assertEqual(economy["quality_delta_pp"], 40.0)
        self.assertEqual(economy["frontier"], ["cost_usd"])

    def test_effort_not_interpolated_or_inherited(self):
        result = build_context(request(), [view(rows=[row(effort="medium")])])
        self.assertEqual(result["excluded"][0]["reason"], "unknown_or_unavailable_effort")
        self.assertEqual(result["tasks"][0]["primary_comparisons"], [])

    def test_cost_from_other_benchmark_not_attached(self):
        result = build_context(request("investigation"), [view("swe-atlas-qna", [row(cost=None)]),
                                                          view("cursorbench", [row(cost=.1)])])
        primary = candidate(cohort(result), "frontier-a", "low")
        self.assertEqual(primary["expenses"], {})
        self.assertEqual(primary["expense_evidence"], "none")
        self.assertEqual(cohort(result, kind="supporting_comparisons")["source_id"], "cursorbench")
        self.assertIn("unknown_primary_expense", result["tasks"][0]["evidence_gaps"])

    def test_sources_disagree_without_an_arbitrary_merged_verdict(self):
        ds = view(rows=[row(cost=1), row("economy-b", "max", .79, 2)])
        fc = view("frontiercode", [row(cost=5, subset="extended"),
                                   row("economy-b", "max", .79, 1, subset="extended")])
        result = build_context(request(), [ds, fc])
        comparisons = result["tasks"][0]["primary_comparisons"]
        self.assertEqual(len(comparisons), 2)
        self.assertEqual([c["source_id"] for c in comparisons], ["deepswe", "frontiercode"])
        self.assertEqual(candidate(comparisons[0], "frontier-a", "low")["frontier"], ["cost_usd"])
        self.assertEqual(candidate(comparisons[1], "economy-b", "max")["frontier"], ["cost_usd"])

    def test_harnesses_not_pooled(self):
        result = build_context(request(), [view(rows=[row(), row(effort="high", harness="different")])])
        self.assertEqual(len(result["tasks"][0]["primary_comparisons"]), 2)

    def test_stale_policy_explicit(self):
        stale = [view(stale=True)]
        self.assertTrue(cohort(build_context(request(), stale))["candidates"])
        refused = build_context(request(allow_stale=False), stale)
        self.assertEqual(refused["tasks"][0]["primary_comparisons"], [])

    def test_unknown_expense_does_not_become_zero(self):
        result = build_context(request(), [view(rows=[row(cost=None)])])
        only = cohort(result)["candidates"][0]
        self.assertEqual(only["expenses"], {})
        self.assertEqual(only["frontier"], [])

    def test_declared_limit_annotates_instead_of_hiding(self):
        result = build_context(request(max_cost_usd=.5), [view(rows=[row(cost=2)])])
        flagged = cohort(result)["candidates"][0]
        self.assertEqual(flagged["constraints"], [{"constraint": "max_cost_usd", "limit": .5,
                                                   "observed": 2, "status": "exceeds"}])
        self.assertEqual(result["declared_constraints"], {"max_cost_usd": .5})

    def test_unknown_value_for_a_declared_limit_is_reported_as_unknown(self):
        result = build_context(request(max_duration_seconds=100), [view(rows=[row()])])
        self.assertEqual(cohort(result)["candidates"][0]["constraints"][0]["status"], "unknown")

    def test_ci_overlap_not_pruned_as_proven_equivalence(self):
        result = build_context(request(), [view(rows=[row(score_low=.7, score_high=.9),
                                                      row("economy-b", "max", .79, 2, score_low=.69, score_high=.89)])])
        self.assertEqual([c["frontier"] for c in cohort(result)["candidates"]], [["cost_usd"], ["cost_usd"]])

    def test_one_call_covers_several_task_types_without_repeating_sources(self):
        result = build_context(request("implementation", "tests"), [view(), view("swe-atlas-tw", [row(cost=None)])])
        self.assertEqual([t["task_type"] for t in result["tasks"]], ["implementation", "tests"])
        self.assertEqual(len(result["sources"]), 2)
        self.assertEqual(len(result["inventory"]), 3)

    def test_brief_keeps_candidates_limits_and_gaps(self):
        result = build_context(request(max_cost_usd=.5), [view(rows=[row(cost=2), row("economy-b", "max", .4, .01)])])
        summary = brief(result)
        kept = cohort(summary)
        self.assertEqual(len(kept["candidates"]), 2)
        self.assertTrue(all(c["constraints"] for c in kept["candidates"]))
        self.assertNotIn("observations", kept)
        self.assertIn("observations", cohort(result))
        self.assertEqual(summary["sources"][0]["row_count"], 2)

    def test_no_verdict_fields_are_produced(self):
        result = build_context(request(), [view()])
        for absent in ("status", "recommended", "winner", "quality_floor", "contraindications"):
            self.assertNotIn(absent, result)
            self.assertNotIn(absent, cohort(result))

    def test_offline_cli_reports_acquisition_state_not_absent_measurements(self):
        with tempfile.TemporaryDirectory() as tmp:
            req = Path(tmp) / "request.json"
            req.write_text(json.dumps(request()), encoding="utf-8")
            process = subprocess.run([sys.executable, "-B", str(SCRIPTS / "benchmark_router.py"),
                                      "--cache-dir", str(Path(tmp) / "cache"), "--offline", "context",
                                      "--request", str(req)], capture_output=True, text=True, check=True)
            payload = json.loads(process.stdout)
            self.assertEqual(payload["data_status"], "offline")
            self.assertEqual(payload["usage"], "diagnostic_only")
            self.assertTrue(payload["tasks"][0]["missing_primary"])


if __name__ == "__main__":
    unittest.main()
