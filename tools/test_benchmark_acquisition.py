"""Acquisition visibility at the recommendation boundary; no model calls."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_benchmark_router import SCRIPTS, any_source, data, guide_data, request, row
from route_evidence.cache import Cache, FetchError
from route_evidence.processes import ProcessScope
from route_evidence.providers import SOURCES
from route_evidence.service import RoutingService


class AcquisitionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.now = 1800000000.0
        self.cache = Cache(Path(self.tmp.name), clock=lambda: self.now)
        self.service = RoutingService(self.cache, client="codex", clock=lambda: self.now)

    async def query(self, task_type="terminal", **kwargs):
        return await self.service.get_routing_context([task_type], available=request()["available"], **kwargs)

    @staticmethod
    def candidates(result, index=0):
        return result["tasks"][0]["primary_comparisons"][index]["candidates"]

    @staticmethod
    def benchmark_calls(fetch):
        # Guides refresh in the same cycle; this counts measurement fetches.
        return sum(1 for call in fetch.call_args_list if call.args[0].get("kind") != "guide")

    async def test_cold_cache_refreshes_then_reuses_until_ttl(self):
        with patch.object(ProcessScope, "fetch", side_effect=any_source) as fetch:
            first = await self.query()
            self.assertEqual(first["data_status"], "ready")
            self.assertEqual(first["usage"], "routing")
            self.assertEqual(first["sources"][0]["refresh"], "updated")
            self.assertEqual(self.benchmark_calls(fetch), 1)
            second = await self.query()
            self.assertEqual(second["data_status"], "ready")
            self.assertEqual(second["sources"][0]["refresh"], "cached")
            self.assertEqual(self.benchmark_calls(fetch), 1)
            self.now += 86400
            third = await self.query()
            self.assertEqual(third["data_status"], "ready")
            self.assertEqual(third["sources"][0]["refresh"], "updated")
            self.assertEqual(self.benchmark_calls(fetch), 2)

    async def test_offline_missing_cache_is_explicit_diagnostic(self):
        self.service.offline = True
        with patch.object(ProcessScope, "fetch", side_effect=AssertionError("offline requested network")):
            for details in (False, True):
                result = await self.query(details=details)
                self.assertEqual(result["tasks"][0]["primary_comparisons"], [])
                self.assertEqual(result["data_status"], "offline")
                self.assertEqual(result["usage"], "diagnostic_only")
                self.assertIn("disabled", result["data_message"])
                self.assertIn("not evidence", result["data_message"])
                self.assertEqual(result["sources"][0]["availability"], "missing")

    async def test_offline_populated_cache_still_cannot_claim_online_routing(self):
        self.cache.get(SOURCES["terminal-bench"], lambda *args: (data("terminal-bench"), {}))
        self.service.offline = True
        result = await self.query()
        self.assertTrue(self.candidates(result))
        self.assertEqual(result["data_status"], "offline")
        self.assertEqual(result["usage"], "diagnostic_only")
        self.assertEqual(result["sources"][0]["availability"], "fresh")

    async def test_fetch_failure_and_backoff_are_visible_without_details(self):
        with patch.object(ProcessScope, "fetch", side_effect=FetchError("fixture network failure")) as fetch:
            first = await self.query()
            self.assertEqual(first["data_status"], "unavailable")
            self.assertIn("not evidence", first["data_message"])
            source = first["sources"][0]
            self.assertEqual(source["availability"], "missing")
            self.assertEqual(source["refresh"], "failed")
            self.assertIn("fixture network failure", source["error"])
            self.assertIsNotNone(source["next_retry_at"])
            second = await self.query()
            self.assertEqual(second["data_status"], "unavailable")
            self.assertEqual(second["sources"][0]["refresh"], "backoff")
            self.assertEqual(self.benchmark_calls(fetch), 1)

    async def test_failed_refresh_with_old_data_is_stale_not_fresh(self):
        self.cache.get(SOURCES["terminal-bench"], lambda *args: (data("terminal-bench"), {}))
        self.now += 86400
        with patch.object(ProcessScope, "fetch", side_effect=FetchError("fixture network failure")):
            result = await self.query()
        self.assertEqual(result["data_status"], "stale")
        self.assertEqual(result["sources"][0]["availability"], "stale")
        self.assertEqual(result["sources"][0]["refresh"], "failed")
        self.assertTrue(self.candidates(result))

    async def test_loaded_but_unmatched_measurements_are_not_a_download_failure(self):
        with patch.object(ProcessScope, "fetch", return_value=(data("terminal-bench", [row(model="unavailable-model")]), {})):
            result = await self.query()
        self.assertEqual(result["tasks"][0]["primary_comparisons"], [])
        self.assertEqual(result["data_status"], "ready")
        self.assertIn("no matching", result["data_message"])
        self.assertEqual(result["sources"][0]["availability"], "fresh")

    async def test_partial_acquisition_identifies_missing_source(self):
        def fetch(source, validators, *, browser):
            if source["id"] == "cursorbench":
                raise FetchError("fixture support unavailable")
            return any_source(source, validators, browser=browser)
        with patch.object(ProcessScope, "fetch", side_effect=fetch):
            result = await self.query("investigation")
        self.assertEqual(result["data_status"], "partial")
        states = {s["source_id"]: s["availability"] for s in result["sources"]}
        self.assertEqual(states, {"cursorbench": "missing", "swe-atlas-qna": "fresh"})
        self.assertTrue(self.candidates(result))
        self.assertEqual(result["tasks"][0]["supporting_comparisons"], [])

    async def test_guide_failure_is_reported_beside_the_measurements(self):
        def fetch(source, validators, *, browser):
            if source.get("kind") == "guide":
                raise FetchError("fixture guide unavailable")
            return data(source["id"]), {}
        with patch.object(ProcessScope, "fetch", side_effect=fetch):
            result = await self.query()
        # A guide that did not load must not look like missing measurements.
        self.assertEqual(result["data_status"], "ready")
        document = result["guidance"]["documents"][0]
        self.assertFalse(document["available"])
        self.assertIn("fixture guide unavailable", document["reason"])
        self.assertIn("not an absence", document["note"])

    async def test_guidance_is_quoted_and_scoped_to_the_client(self):
        with patch.object(ProcessScope, "fetch", side_effect=any_source):
            result = await self.query()
        guidance = result["guidance"]
        self.assertEqual(guidance["evidence_type"], "vendor_guidance")
        self.assertEqual(guidance["scope"], "client")
        self.assertEqual([d["guide_id"] for d in guidance["documents"]], ["openai-reasoning"])
        document = guidance["documents"][0]
        self.assertEqual(document["applies_to"], ["codex"])
        self.assertEqual(document["publisher"], "OpenAI")
        self.assertEqual(len(document["sections"]), 2)
        self.assertEqual(document["document_caveats"][0]["kind"], "note")
        self.assertTrue(document["content_hash"])
        self.assertIn("not an independent measurement", guidance["note"])

    async def test_missing_inventory_does_not_pretend_refresh_was_checked(self):
        with patch.object(ProcessScope, "fetch", side_effect=AssertionError("not a valid request")):
            result = await self.service.get_routing_context(["terminal"])
        self.assertEqual(result["status"], "needs_inventory")
        self.assertEqual(result["data_status"], "not_checked")
        self.assertEqual(result["usage"], "setup_required")


class AcquisitionCLITests(unittest.TestCase):
    def test_cli_does_not_drop_offline_diagnostic_notice(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run([sys.executable, "-B", str(SCRIPTS / "benchmark_router.py"),
                "--cache-dir", tmp, "--offline", "context", "--request", "-"],
                input=json.dumps(request("terminal")), capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("DIAGNOSTIC ONLY", proc.stderr)
        self.assertIn("disables source refresh", proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["data_status"], "offline")
        self.assertEqual(result["usage"], "diagnostic_only")
        self.assertIn("disabled", result["data_message"])


if __name__ == "__main__":
    unittest.main()
