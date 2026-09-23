"""Synthetic discovery and acquisition contracts, not live model evaluations."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "route-subagents" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from route_evidence.cache import Cache, FetchError, INVENTORY_REFRESH_INTERVAL, MAX_INVENTORY_KEYS, source_lock
from route_evidence.core import EvidenceError, encoded, identity, timestamp
from route_evidence.model_names import inventory_keys, matching_diagnostics, model_identity, resolve_model
from route_evidence.providers import Fetcher, SOURCES, parse_tables, snapshot
from route_evidence.routing import brief, build_context
from route_evidence import terminal_hub as hub


def inventory(*models, efforts=("medium",)):
    return [{"model": name, "efforts": list(efforts)} for name in models]


def row(model="future-model", effort="medium", **extra):
    return {"model": model, "effort": effort, "harness": "fixture", "subset": "all",
            "metric": "pass_at_1", "protocol": "synthetic", "score": .8, **extra}


def data(source="cursorbench", rows=None):
    return snapshot(SOURCES[source], [row()] if rows is None else rows)


def context(rows, available, *, source="cursorbench", stale=False, **extra):
    request = {"client": "codex", "task_types": ["terminal" if source == "terminal-bench" else "implementation"],
               "available": available, **extra}
    view = {"source_id": source, "source_url": SOURCES[source]["url"], "stale": stale,
            "snapshot": data(source, rows) if rows is not None else None}
    return build_context(request, [view])


class NameMatchingTests(unittest.TestCase):
    def test_cursor_alias_is_reversible_and_effort_is_separate(self):
        rows = parse_tables(SOURCES["cursorbench"], [[
            ["Model", "Score", "Cost / Task", "Tokens / Task", "Steps / Task"],
            ["Opus 5.5 Medium", "80%", "$1.20", "1000", "20"]]])
        self.assertEqual(rows[0]["model"], "Opus 5.5")
        self.assertEqual(rows[0]["effort"], "medium")
        self.assertEqual(rows[0]["model_identity"]["canonical_model"], "claude-opus-5-5")
        result = context(rows, inventory("claude-opus-5-5"))
        candidates = result["tasks"][0]["supporting_comparisons"][0]["candidates"]
        self.assertEqual([(c["model"], c["effort"]) for c in candidates], [("claude-opus-5-5", "medium")])
        match = result["sources"][0]["model_matching"]["models"][0]
        self.assertEqual(match["matched_names"][0]["source_model"], "Opus 5.5")
        self.assertEqual(match["status"], "matched")

    def test_no_fuzzy_version_family_provider_or_tier_resolution(self):
        for label in ("Opus 5.50", "Opus 5.5 fast", "Opus 5.5 20260922", "Opus latest", "anthropic/Opus 5.5", "GPT-5.6 Luna"):
            with self.subTest(label=label):
                result = context([row(label)], inventory("claude-opus-5-5", "gpt-6-luna"))
                self.assertFalse(result["tasks"][0]["supporting_comparisons"])
        self.assertEqual(model_identity("frontiercode", "Opus 5.5")["canonical_model"], "Opus 5.5")

    def test_new_exact_model_needs_no_registry_entry(self):
        result = context([row("Unseen Release 17.2")], inventory("unseen-release-17-2"))
        self.assertEqual(result["sources"][0]["model_matching"]["models"][0]["usable_rows"], 1)

    def test_confirmed_caller_alias_is_preserved(self):
        available = [{"model": "native-opus", "evidence_names": ["claude-opus-5-5"], "efforts": ["medium"]}]
        result = context([row("Opus 5.5")], available)
        self.assertEqual(result["tasks"][0]["supporting_comparisons"][0]["candidates"][0]["model"], "native-opus")

    def test_reviewed_and_caller_bindings_cannot_choose_different_models(self):
        available = [{"model": "other", "evidence_names": ["Opus 5.5"], "efforts": ["medium"]},
                     *inventory("claude-opus-5-5")]
        result = context([row("Opus 5.5")], available)
        self.assertFalse(result["tasks"][0]["supporting_comparisons"])
        self.assertEqual(result["excluded"][0]["reason"], "ambiguous_model_identity")
        self.assertEqual(result["sources"][0]["model_matching"]["ambiguous_names"], ["Opus 5.5"])

    def test_source_annotation_cannot_forge_a_mapping(self):
        result = context([row("wrong-model", model_identity={"canonical_model": "claude-opus-5-5"})], inventory("claude-opus-5-5"))
        self.assertFalse(result["tasks"][0]["supporting_comparisons"])

    def test_diagnostics_distinguish_acquisition_name_effort_and_harness(self):
        for rows, kwargs, expected in (
            (None, {}, "source_unavailable"),
            ([row("another")], {}, "no_matching_model_name"),
            ([row(effort=None)], {}, "no_matching_effort"),
            ([row(effort="max")], {}, "no_matching_effort"),
            ([row()], {"harness": "not-this-harness"}, "harness_filtered"),
            ([row()], {"stale": True, "allow_stale": False}, "stale_disallowed"),
        ):
            with self.subTest(expected=expected):
                result = context(rows, inventory("future-model"), **kwargs)
                self.assertEqual(result["sources"][0]["model_matching"]["models"][0]["status"], expected)

    def test_compact_context_retains_diagnostics_not_raw_rows(self):
        result = context([row("Opus 5.5")], inventory("claude-opus-5-5"))
        self.assertEqual(brief(result)["sources"], result["sources"])
        self.assertNotIn("observations", brief(result)["tasks"][0]["supporting_comparisons"][0])

    def test_unrelated_name_examples_are_bounded_but_count_is_honest(self):
        result = matching_diagnostics("cursorbench", [row("unrelated-%d" % i) for i in range(30)], inventory("future-model"))
        self.assertEqual(result["unmatched_name_count"], 30)
        self.assertEqual(len(result["unmatched_name_examples"]), 12)
        self.assertTrue(result["unmatched_names_truncated"])

    def test_normalization_cannot_duplicate_measurements(self):
        with self.assertRaisesRegex(EvidenceError, "multiple evidence labels"):
            context([row("Opus 5.5"), row("claude-opus-5-5")], inventory("claude-opus-5-5"))


class InventoryRefreshTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.now = 1800000000.0
        self.cache = Cache(Path(self.tmp.name), clock=lambda: self.now)
        self.source = SOURCES["deepswe"]
        self.fetch = Mock(side_effect=lambda *args: (data("deepswe"), {}))
        self.a = inventory_keys(inventory("a"))
        self.ab = inventory_keys(inventory("a", "b"))

    def get(self, keys, **kwargs):
        return self.cache.get(self.source, self.fetch, inventory_keys=keys, **kwargs)

    def test_new_inventory_refreshes_fresh_source_once_even_when_model_absent(self):
        self.assertEqual(self.get(self.a)["refresh"], "updated")
        self.assertEqual(self.get(self.ab)["refresh_reason"], "inventory_changed")
        self.assertEqual(self.get(self.ab)["refresh"], "cached")
        self.assertEqual(self.fetch.call_count, 2)

    def test_fingerprints_ignore_order_and_removed_models(self):
        self.assertEqual(self.ab, inventory_keys(inventory("b", "a")))
        self.get(self.ab)
        self.assertEqual(self.get(self.a)["refresh"], "cached")
        self.assertEqual(self.fetch.call_count, 1)
        self.assertEqual(inventory_keys(inventory("a", efforts=("low", "high"))),
                         inventory_keys(inventory("a", efforts=("high", "low"))))

    def test_changed_supported_effort_and_alias_are_new_inventory(self):
        self.get(self.a)
        new = inventory_keys([{"model": "a", "efforts": ["medium", "max"], "evidence_names": ["published-a"]}])
        self.assertEqual(self.get(new)["refresh_reason"], "inventory_changed")

    def test_successful_304_consumes_probe_without_faking_new_data(self):
        first = self.get(self.a)
        self.now += 5
        self.fetch.side_effect = lambda *args: (None, {})
        refreshed = self.get(self.ab)
        self.assertEqual(refreshed["refresh"], "validated_not_modified")
        self.assertEqual(refreshed["data_changed_at"], first["data_changed_at"])
        self.assertEqual(self.get(self.ab)["refresh"], "cached")

    def test_reconnect_does_not_repeat_checked_inventory(self):
        self.get(self.a); self.get(self.ab)
        self.cache = Cache(Path(self.tmp.name), clock=lambda: self.now)
        self.assertEqual(self.get(self.ab)["refresh"], "cached")
        self.assertEqual(self.fetch.call_count, 2)

    def test_inventory_churn_is_deferred_not_dropped(self):
        self.get(self.a); self.get(self.ab)
        abc = inventory_keys(inventory("a", "b", "c"))
        result = self.get(abc)
        self.assertEqual(result["refresh"], "inventory_deferred")
        self.assertIn("next_inventory_refresh_at", result)
        self.now += INVENTORY_REFRESH_INTERVAL
        self.assertEqual(self.get(abc)["refresh_reason"], "inventory_changed")
        self.assertEqual(self.fetch.call_count, 3)

    def test_retry_after_wins_over_inventory_and_force(self):
        self.get(self.a)
        self.fetch.side_effect = FetchError("fixture throttled", retry_after=900)
        failed = self.get(self.ab)
        self.assertEqual(failed["refresh"], "failed")
        self.assertEqual(self.get(inventory_keys(inventory("c")), force=True)["refresh"], "backoff")
        self.assertEqual(self.fetch.call_count, 2)
        self.assertEqual(self.get(self.ab)["snapshot"], failed["snapshot"])
        self.now += 900
        self.fetch.side_effect = lambda *args: (data("deepswe"), {})
        self.assertEqual(self.get(self.ab)["refresh"], "updated")

    def test_offline_and_lock_contention_never_consume_probe(self):
        self.get(self.a)
        self.assertEqual(self.get(self.ab, offline=True)["refresh"], "offline")
        with source_lock(Path(self.tmp.name) / (self.source["id"] + ".lock")) as acquired:
            self.assertTrue(acquired)
            self.assertEqual(self.get(self.ab)["refresh"], "update_in_progress")
        self.assertEqual(self.get(self.ab)["refresh_reason"], "inventory_changed")
        self.assertEqual(self.fetch.call_count, 2)

    def test_cancellation_keeps_last_good_and_probe_cooldown(self):
        first = self.get(self.a)
        self.fetch.side_effect = FetchError("refresh_cancelled")
        self.assertEqual(self.get(self.ab)["refresh"], "cancelled")
        self.assertEqual(self.get(self.ab)["refresh"], "inventory_deferred")
        state = self.cache.read(self.source)
        self.assertFalse(state.get("next_retry_at"))
        self.assertEqual(state["snapshot"], first["snapshot"])
        self.assertEqual(self.fetch.call_count, 2)

    def test_old_cache_gets_one_check_not_an_implicit_old_inventory(self):
        self.cache.get(self.source, self.fetch)
        self.assertEqual(self.get(self.a)["refresh_reason"], "inventory_changed")
        self.assertEqual(self.get(self.a)["refresh"], "cached")

    def test_malformed_keys_are_rejected(self):
        with self.assertRaises(EvidenceError):
            self.get(["unbounded arbitrary task prose"])
        self.assertEqual(self.fetch.call_count, 0)

    def test_fresh_data_during_backoff_is_reported_cached(self):
        self.get(self.a)
        self.fetch.side_effect = FetchError("fixture throttled", retry_after=900)
        self.assertEqual(self.get(self.a, force=True)["refresh"], "failed")
        self.assertEqual(self.get(self.a)["refresh"], "cached")
        self.assertEqual(self.get(self.a, force=True)["refresh"], "backoff")
        self.assertEqual(self.fetch.call_count, 2)

    def test_full_check_history_evicts_the_oldest_checks(self):
        batches = [["%064x" % (100 * b + i) for i in range(100)] for b in range(3)]
        for batch in batches:
            self.get(batch)
            self.now += INVENTORY_REFRESH_INTERVAL
        checked = self.cache.read(self.source)["inventory_checked"]
        self.assertEqual(len(checked), MAX_INVENTORY_KEYS)
        self.assertLessEqual(set(batches[1] + batches[2]), set(checked))
        self.assertNotIn(batches[0][-1], checked)
        self.assertEqual(self.fetch.call_count, 3)


def hub_row(i=0, **extra):
    return {"id": "row-%d" % i, "status": "display",
            "metadata": {"model_display": {"label": "model-%d" % i}, "agent_display": {"label": "fixture-agent"},
                         "reasoning_effort": "medium", "date": "2026-09-22"},
            "metrics": {"accuracy": 80, "accuracy_ci95_half_width": 2, "n_trials": 100,
                        "total_cost_usd": 500, "total_tokens": 100000, "output_tokens": 5000}, **extra}


def hub_page(rows=None, *, total=1, page=1):
    return {"leaderboard": {"id": hub.BOARD_ID, "name": hub.BOARD_NAME, "package": hub.PACKAGE,
                            "title": "Terminal-Bench 4.0", "visibility": "public", "updated_at": "2026-09-22T00:00:00Z"},
            "rows": [hub_row()] if rows is None else rows,
            "pagination": {"total": total, "total_pages": (total + hub.PAGE_SIZE - 1) // hub.PAGE_SIZE,
                           "page": page, "page_size": hub.PAGE_SIZE}}


class HubSourceTests(unittest.TestCase):
    def run_pages(self, *pages, **kwargs):
        reader = Mock(side_effect=[encoded(p) for p in pages])
        result = hub.fetch_snapshot(SOURCES["terminal-bench"], timeout=10, reader=reader, **kwargs)
        return result, reader

    def test_api_preserves_units_identity_and_unknown_per_task_cost(self):
        result, reader = self.run_pages(hub_page())
        measured = result["rows"][0]
        self.assertAlmostEqual(measured["score"], .8)
        self.assertAlmostEqual(measured["score_low"], .78)
        self.assertEqual(measured["effort"], "medium")
        self.assertIsNone(measured["evaluated_at"])
        self.assertIsNone(measured["cost_usd"])
        self.assertIsNone(measured["total_tokens"])
        self.assertEqual(measured["aggregate_usage"]["total_cost_usd"], 500)
        self.assertEqual(result["acquisition"]["url"], hub.ENDPOINT)
        self.assertEqual(reader.call_args.args[0], {"leaderboard_id": hub.BOARD_ID, "page": 1, "page_size": 100})

    def test_two_pages_deliver_every_row_once(self):
        result, reader = self.run_pages(hub_page([hub_row(i) for i in range(100)], total=101),
                                       hub_page([hub_row(100)], total=101, page=2))
        self.assertEqual(len(result["rows"]), 101)
        self.assertEqual(reader.call_count, 2)
        self.assertEqual(result["acquisition"]["reported_rows"], 101)

    def test_wrong_version_private_board_or_missing_pagination_are_refused(self):
        for field, value in (("id", "wrong-id"), ("name", "2-0-0"), ("visibility", "private"), ("package", "other/board")):
            p = hub_page(); p["leaderboard"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(FetchError, "identity"):
                self.run_pages(p)
        p = hub_page(); del p["pagination"]
        with self.assertRaisesRegex(FetchError, "pagination"):
            self.run_pages(p)

    def test_partial_and_duplicate_pages_are_refused(self):
        with self.assertRaisesRegex(FetchError, "incomplete_page"):
            self.run_pages(hub_page(total=101))
        with self.assertRaisesRegex(FetchError, "duplicate_row_id"):
            self.run_pages(hub_page([hub_row(i) for i in range(100)], total=101), hub_page([hub_row(0)], total=101, page=2))

    def test_changed_board_during_pagination_is_refused(self):
        second = hub_page([hub_row(100)], total=101, page=2)
        second["leaderboard"]["updated_at"] = "2026-09-22T00:01:00Z"
        with self.assertRaisesRegex(FetchError, "changed_during"):
            self.run_pages(hub_page([hub_row(i) for i in range(100)], total=101), second)

    def test_hidden_rows_and_unspecified_effort_are_not_invented(self):
        visible = hub_row(); visible["metadata"]["reasoning_effort"] = ""
        result, _ = self.run_pages(hub_page([visible, hub_row(1, status="hide")], total=2))
        self.assertEqual(len(result["rows"]), 1)
        self.assertIsNone(result["rows"][0]["effort"])

    def test_invalid_numbers_and_unknown_visibility_fail(self):
        for value in (float("nan"), -1, 101, True):
            p = hub_page(); p["rows"][0]["metrics"]["accuracy"] = value
            with self.subTest(value=value), self.assertRaises((EvidenceError, ValueError)):
                self.run_pages(p)
        with self.assertRaisesRegex(FetchError, "unknown_row_status"):
            self.run_pages(hub_page([hub_row(status="pending")]))

    def test_byte_and_time_budgets_are_not_per_page(self):
        with patch.object(hub, "MAX_BYTES", 10), self.assertRaisesRegex(FetchError, "too_large"):
            self.run_pages(hub_page())
        with self.assertRaisesRegex(FetchError, "deadline"):
            self.run_pages(hub_page(), clock=Mock(side_effect=[0, 11]))

    def test_http_request_is_anonymous_read_and_contains_no_bearer(self):
        response = Mock(); response.read.return_value = encoded(hub_page())
        response.__enter__ = Mock(return_value=response); response.__exit__ = Mock(return_value=False)
        opener = Mock(); opener.open.return_value = response
        with patch.object(hub.urllib.request, "build_opener", return_value=opener):
            hub.fetch_page({"leaderboard_id": hub.BOARD_ID, "page": 1, "page_size": 100}, 2)
        req = opener.open.call_args.args[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.full_url, hub.ENDPOINT)
        self.assertFalse(any(key.lower() in ("authorization", "cookie") for key in req.headers))
        self.assertEqual(req.get_header("Apikey"), hub.PUBLISHABLE_KEY)

    def test_api_is_preferred_with_browser_off_and_provenance_survives_brief(self):
        with patch.object(hub, "fetch_page", return_value=encoded(hub_page())), patch.object(Fetcher, "browser_snapshot", side_effect=AssertionError("browser must not run")):
            snapshot_data, validators = Fetcher()(SOURCES["terminal-bench"], {})
        request = {"client": "codex", "task_types": ["terminal"], "available": inventory("model-0")}
        result = build_context(request, [{"source_id": "terminal-bench", "snapshot": snapshot_data, "stale": False}])
        self.assertEqual(brief(result)["sources"][0]["acquisition"]["kind"], "publisher_json_api")

    def test_browser_fallback_requires_opt_in_and_keeps_preferred_failure(self):
        with patch.object(hub, "fetch_snapshot", side_effect=hub.HubUnavailable("fixture unavailable")):
            with self.assertRaises(hub.HubUnavailable):
                Fetcher()(SOURCES["terminal-bench"], {})
            with patch.object(Fetcher, "browser_snapshot", return_value=data("terminal-bench")) as browser:
                result, _ = Fetcher(browser=True)(SOURCES["terminal-bench"], {})
                self.assertEqual(browser.call_count, 1)
                self.assertEqual(result["acquisition"]["kind"], "browser_fallback")
                self.assertIn("fixture unavailable", result["warnings"][-1])

    def test_never_fallback_around_throttling_access_or_semantic_failure(self):
        for error in (FetchError("terminal_hub_http_429", 300), FetchError("terminal_hub_http_403"),
                      FetchError("terminal_hub_board_identity_changed"), hub.HubUnavailable("terminal_hub_http_503", 60)):
            with self.subTest(error=error), patch.object(hub, "fetch_snapshot", side_effect=error), patch.object(Fetcher, "browser_snapshot", side_effect=AssertionError("must not bypass")):
                with self.assertRaises(FetchError):
                    Fetcher(browser=True)(SOURCES["terminal-bench"], {})


class EvolutionIntegrationTests(unittest.IsolatedAsyncioTestCase):
    """Run with the complete repository through ordinary tools/test_*.py discovery."""
    async def test_service_refresh_and_aliases_reach_compact_advisor_evidence(self):
        from route_evidence.service import RoutingService
        from route_evidence.processes import ProcessScope
        from route_evidence.advice import _project_evidence, _expand_records
        from route_evidence.guides import guide_snapshot
        with tempfile.TemporaryDirectory() as tmp:
            now = 1800000000.0
            service = RoutingService(Cache(Path(tmp), clock=lambda: now), client="codex", clock=lambda: now)
            calls = []
            def fetch(source, validators, *, browser=False):
                calls.append(source["id"])
                if source.get("kind") == "guide":
                    body = "# Synthetic guide\n\n" + "\n\n".join("## " + h + "\nFixture prose." for h in source["sections"])
                    return guide_snapshot(source, body), {}
                rows = [row("old-model")]
                if source["id"] == "cursorbench" and calls.count("cursorbench") > 1:
                    rows.append(row("Opus 5.5"))
                return snapshot(source, rows), {}
            with patch.object(ProcessScope, "fetch", side_effect=fetch):
                await service.get_routing_context(["implementation"], available=inventory("old-model"))
                result = await service.get_routing_context(["implementation"], available=inventory("old-model", "claude-opus-5-5"))
                again = await service.get_routing_context(["implementation"], available=inventory("claude-opus-5-5", "old-model"))
            self.assertEqual(calls.count("cursorbench"), 2)
            self.assertEqual(calls.count("openai-reasoning"), 1)
            source = next(s for s in result["sources"] if s["source_id"] == "cursorbench")
            self.assertEqual(source["refresh_reason"], "inventory_changed")
            self.assertEqual(source["model_matching"]["models"][0]["status"], "matched")
            candidates = [{"model": a["model"], "effort": e} for a in inventory("old-model", "claude-opus-5-5") for e in a["efforts"]]
            projected = _project_evidence(again, candidates)
            restored = _expand_records(projected["sources"])
            self.assertEqual(next(s for s in restored if s["source_id"] == "cursorbench")["model_matching"], source["model_matching"])
            self.assertTrue(any(c["model"] == "claude-opus-5-5" for t in again["tasks"] for cohort in t["supporting_comparisons"] for c in cohort["candidates"]))

    async def test_new_inventory_skips_a_source_this_host_cannot_fetch(self):
        from route_evidence.service import RoutingService
        from route_evidence.processes import ProcessScope
        from route_evidence.guides import guide_snapshot
        now = 1800000000.0
        for browser, frontier_calls, refresh in ((False, 1, "cached"), (True, 2, "updated")):
            calls = []
            def fetch(source, validators, *, browser=False):
                calls.append(source["id"])
                if source.get("kind") == "guide":
                    body = "# Synthetic guide\n\n" + "\n\n".join("## " + h + "\nFixture prose." for h in source["sections"])
                    return guide_snapshot(source, body), {}
                return snapshot(source, [row("old-model")]), {}
            with self.subTest(browser=browser), tempfile.TemporaryDirectory() as tmp, \
                    patch.object(ProcessScope, "fetch", side_effect=fetch):
                def service(enabled):
                    return RoutingService(Cache(Path(tmp), clock=lambda: now), client="codex",
                                          clock=lambda: now, browser=enabled)
                # A browser-enabled run left a fresh snapshot for the old inventory.
                await service(True).get_routing_context(["implementation"], available=inventory("old-model"))
                result = await service(browser).get_routing_context(
                    ["implementation"], available=inventory("old-model", "new-model"))
                frontier = next(s for s in result["sources"] if s["source_id"] == "frontiercode")
                self.assertEqual(calls.count("frontiercode"), frontier_calls)
                self.assertEqual(frontier["refresh"], refresh)
                self.assertEqual(calls.count("deepswe"), 2)


if __name__ == "__main__":
    unittest.main()
