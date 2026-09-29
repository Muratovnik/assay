"""Cost-quality and privacy contracts. Fixtures have independently specified outcomes."""
from __future__ import annotations

import asyncio
import copy
import io
import importlib.metadata
import json
from pathlib import Path
import sys
import subprocess
import threading
import tarfile
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "route-subagents" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from route_evidence.core import EvidenceError
from route_evidence.task_costs import chain_totals, compare, estimates
from route_evidence.task_evidence import TaskEvidence, public_coverage
from route_evidence.task_evaluation import evaluate, forecast
from route_evidence.task_import import llmrouterbench
from route_evidence.advice_contracts import candidate_id, validate_routing_snapshot
from route_evidence.cache import Cache
from route_evidence.service import RoutingService
from route_evidence.routing import build_context
from route_evidence.advisors.jev import _external_state

AVAILABLE = [{"model": "economy", "efforts": ["low"]}, {"model": "capable", "efforts": ["high"]}]
CANDIDATES = [{"model": a["model"], "effort": a["efforts"][0], "candidate_id": candidate_id(a["model"], a["efforts"][0])} for a in AVAILABLE]
PACKET = {"packet_id": "fix", "task_types": ["implementation"], "features": {}, "baseline": {"model": "capable", "effort": "high"}}


def observation(model="economy", expense=2, score=1, scope="chain"):
    return {"model": model, "effort": "low" if model == "economy" else "high", "metric": "accepted",
            "comparison_basis": "same-harness", "score": score, "cost_scope": scope,
            "costs": {"api_usd": expense}, "unit_basis": {"api_usd": "price-revision"}, "complete": True}


def corpus():
    return {"schema_version": 1, "source": {"id": "fixture", "revision": "r1", "license": "CC0-1.0",
            "use": "local-only", "url": "https://example.org/fixture"}, "records": [
        {"task_id": "task1", "task_types": ["implementation"], "features": {},
         "query": "repair asynchronous cache invalidation", "observations": [observation(scope="response")]}]}


def cost_chain():
    return {"schema_version": 1, "complete": True, "initial_route": {"model": "economy", "effort": "low"},
            "comparison_basis": "harness-v1", "unit_basis": {"api_usd": "price-revision"}, "events": [
                {"event_id": category, "category": category, "resources": {"api_usd": price}}
                for category, price in [("routing", 1), ("worker", 2), ("verification", 3), ("coordination", 4)]]}


class CostTests(unittest.TestCase):
    def test_full_chain_cost_and_partial_units(self):
        chain = cost_chain()
        chain["events"].append({"event_id": "worker-retry", "category": "worker", "resources": {"api_usd": 8}})
        total = chain_totals(chain)
        self.assertEqual(total["totals"]["api_usd"], 18)
        self.assertEqual(total["components"]["worker"]["api_usd"], 10)
        chain["events"][-1]["resources"]["api_usd"] = None
        self.assertIsNone(chain_totals(chain)["totals"]["api_usd"])
        chain["events"][-1]["event_id"] = "worker"
        with self.assertRaisesRegex(EvidenceError, "duplicate"):
            chain_totals(chain)

    def test_paired_cost_quality_and_overhead(self):
        rows = [{"task_id": str(i), **observation(model, cost)} for i in range(4)
                for model, cost in [("economy", 18), ("capable", 12)]]
        base = CANDIDATES[1]["candidate_id"]
        self.assertIsNone(compare(rows, CANDIDATES, base, "api_usd", 1)["recommended"])
        for row in rows:
            if row["model"] == "economy":
                row["costs"]["api_usd"] = 8
        self.assertEqual(compare(rows, CANDIDATES, base, "api_usd", 1)["net_benefit"], 3)
        self.assertIsNone(compare(rows, CANDIDATES, base, "api_usd", 5)["recommended"])
        rows[0]["score"] = 0
        self.assertIsNone(compare(rows, CANDIDATES, base, "api_usd", 0)["recommended"])
        for row in rows:
            row["cost_scope"] = "response"
        self.assertIsNone(compare(rows, CANDIDATES, base, "api_usd", 0)["recommended"])
        self.assertIsNone(compare(rows, CANDIDATES, base, "quota_units", None)["recommended"])

    def test_unknown_outcome_and_failed_chains_not_dropped(self):
        rows = [{"task_id": str(i), **observation(expense=cost, score=score)}
                for i, (cost, score) in enumerate([(2, 1), (18, 0), (10, None)])]
        group = estimates(rows, CANDIDATES)[0]["groups"][0]
        self.assertEqual(group["expected_cost"]["api_usd"]["mean"], 10)
        self.assertEqual(group["unknown_quality"], 1)
        self.assertEqual(group["quality"]["mean"], .5)
        self.assertEqual(group["status"], "insufficient_coverage")

    def test_duplicates_wrong_tariff_and_all_fail_cannot_justify_savings(self):
        rows = [{"task_id": str(i), **observation(m, c, score=0)} for i in range(3)
                for m,c in [("economy", 1), ("capable", 10)]]
        base = CANDIDATES[1]["candidate_id"]
        self.assertIsNone(compare(rows, CANDIDATES, base, "api_usd", 0)["recommended"])
        for r in rows:
            r["score"] = 1
        self.assertIsNone(compare(rows, CANDIDATES, base, "api_usd", 0, unit_basis="other-tariff")["recommended"])
        self.assertIsNone(compare(rows + [rows[0]], CANDIDATES, base, "api_usd", 0)["recommended"])

    def test_chronological_forecast_exposes_expensive_late_failure(self):
        rows = [{"task_id": str(i), "observed_at": f"2026-09-{i+1:02}T00:00:00Z", **observation(expense=expense)}
                for i,expense in enumerate([2, 2, 2, 20])]
        report = forecast(rows)["reports"][0]
        self.assertEqual(report["predicted_chains"], 1)
        self.assertEqual(report["mean_absolute_error"], 18)
        self.assertEqual(report["largest_underestimate"], 18)

    def test_held_out_deduplication_and_incomplete_pool(self):
        doc = corpus()
        doc["records"] = [{**copy.deepcopy(doc["records"][0]), "task_id": f"t{i}",
            "query": f"fix cache transaction number {i}",
            "observations": [observation("economy", 2), observation("capable", 10)]} for i in range(8)]
        report = evaluate(doc, overhead=1)["reports"][0]
        # Train chooses the cheaper fixed baseline already: no fictitious savings.
        self.assertEqual(report["train_tasks"], 4)
        self.assertEqual(report["net_saving_per_task"], -1)
        doc["records"].append({**copy.deepcopy(doc["records"][0]), "task_id": "duplicate"})
        self.assertEqual(evaluate(doc)["reports"][0]["train_tasks"], 4)
        doc["records"][-1]["observations"][0]["score"] = 0
        with self.assertRaisesRegex(EvidenceError, "conflicting"):
            evaluate(doc)
        rows = [{"task_id": "a", **observation(score=0)}, {"task_id": "b", **observation(score=None)}]
        self.assertEqual(public_coverage(rows)[0]["all_fail_tasks"], 1)


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = TaskEvidence(self.root, {"enabled": True})

    def test_historical_models_supply_evidence_without_current_route_matches(self):
        doc = corpus()
        doc["records"][0]["observations"] = [
            {**observation("older-model", 2, score=1, scope="response"), "effort": None},
            {**observation("other-old-model", 7, score=0, scope="response"), "effort": None}]
        self.store.install(doc)
        reply = self.store.summarize([PACKET], CANDIDATES, {"fix": "cache invalidation"})
        packet = reply["packets"][0]
        self.assertEqual(packet["public"], [])
        self.assertEqual(packet["unknown_current_candidates"]["public"], "all")
        group = packet["public_coverage"][0]
        self.assertEqual(group["cost_scope"], "response")
        table = [dict(zip(group["columns"], row)) for row in group["rows"]]
        self.assertEqual([r["model"] for r in table], ["older-model", "other-old-model"])
        self.assertEqual(table[0]["mean_score"], 1)
        self.assertEqual(table[1]["mean_score"], 0)
        self.assertEqual(table[0]["mean_costs"], [2])
        self.assertIsNone(table[0]["effort"])
        self.assertIsNone(packet["comparison"]["recommended"])

    def test_full_current_inventory_does_not_crowd_out_public_evidence(self):
        doc = corpus()
        doc["records"][0]["observations"] = [
            {**observation(f"historical-{i}", i+1, scope="response"), "effort": None} for i in range(13)]
        self.store.install(doc)
        current = [{"model": f"current-{i}", "effort": "low", "candidate_id": candidate_id(f"current-{i}", "low")} for i in range(64)]
        reply = self.store.summarize([PACKET], current, {"fix": "cache invalidation"})
        self.assertEqual(reply["status"], "available")
        self.assertEqual(len(reply["packets"][0]["public_coverage"][0]["rows"]), 13)
        self.assertEqual(reply["packets"][0]["unknown_current_candidates"], {"public":"all", "local":"all"})

    def test_idempotent_import_no_match_and_identity(self):
        first = self.store.install(corpus())
        self.assertEqual(first, self.store.install(corpus()))
        result = self.store.summarize([PACKET], CANDIDATES, {"fix": "cache invalidation"})
        self.assertEqual(result["packets"][0]["neighbors"], 1)
        self.assertNotIn("repair asynchronous", json.dumps(result))
        self.assertEqual(result["packets"][0]["public"][0]["groups"][0]["cost_scope"], "response")
        self.assertEqual(self.store.summarize([PACKET], CANDIDATES, {"fix": "gardening"})["packets"][0]["status"], "no_match")
        path = self.root / "task-evidence" / "corpus.json"
        document = json.loads(path.read_text())
        document["corpus"]["records"][0]["observations"][0]["score"] = 0
        path.write_text(json.dumps(document))
        self.assertEqual(self.store.summarize([PACKET], CANDIDATES)["status"], "unavailable")

    def test_import_adapter_nulls_and_archive_links(self):
        release = self.root / "release" / "livecodebench" / "test" / "economy"
        release.mkdir(parents=True)
        (release / "r.json").write_text(json.dumps({"records": [{"index": 1, "origin_query": "cache invalidation", "score": None, "cost": None}]}))
        manifest = {"source": corpus()["source"], "datasets": {"livecodebench": {
            "task_types": ["implementation"], "metric": "pass-at-1", "harness": "unknown", "efforts": {}}}}
        imported = llmrouterbench(self.root / "release", manifest)
        obs = imported["records"][0]["observations"][0]
        self.assertIsNone(obs["score"])
        self.assertIsNone(obs["effort"])
        self.assertIsNone(obs["costs"]["api_usd"])
        archive = self.root / "bad.tar"
        with tarfile.open(archive, "w") as stream:
            link = tarfile.TarInfo("livecodebench/link")
            link.type, link.linkname = tarfile.SYMTYPE, "../outside"
            stream.addfile(link)
        with self.assertRaisesRegex(EvidenceError, "links"):
            llmrouterbench(archive, manifest)

    def test_disabled_and_single_route_do_not_load_encoder(self):
        self.store.config.update(mode="semantic")
        with patch.object(self.store, "load", side_effect=AssertionError("fixed route must not read corpus")):
            self.assertEqual(self.store.summarize([{**PACKET, "explicit": PACKET["baseline"]}], CANDIDATES)["packets"][0]["status"], "skipped_fixed_route")
        self.store.config["enabled"] = False
        self.assertEqual(self.store.summarize([PACKET], CANDIDATES)["status"], "disabled")

    def test_cli_import_query_forecast_and_opt_out(self):
        config = self.root / "config.json"
        config.write_text(json.dumps({"schema_version": 2, "client": "test", "task_evidence": {"enabled": True}}))
        source = self.root / "input.json"
        source.write_text(json.dumps(corpus()))
        argv = [sys.executable, "-B", str(SCRIPTS / "benchmark_router.py"), "--config", str(config), "--cache-dir", str(self.root)]
        def call(command, data=None):
            p = subprocess.run(argv+command, input=json.dumps(data) if data is not None else None,
                               capture_output=True, text=True, timeout=10)
            self.assertEqual(p.returncode, 0, p.stderr+p.stdout)
            return json.loads(p.stdout)
        call(["task-import", "--file", str(source)])
        request = {"packets": [PACKET], "available": AVAILABLE, "task_queries": {"fix": "cache invalidation"}}
        reply = call(["task-context", "--request", "-"], request)
        self.assertEqual(reply["packets"][0]["neighbors"], 1)
        self.assertEqual(call(["task-forecast", "--request", "-"], {"packets": [PACKET]})["packets"][0]["reports"], [])
        config.write_text(json.dumps({"schema_version": 2, "client": "test"}))
        self.assertEqual(call(["task-context", "--request", "-"], request)["status"], "disabled")


class IntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = time.time()
        self.config = {"schema_version": 2, "task_evidence": {"enabled": True, "deadline_seconds": 5}}
        self.service = RoutingService(Cache(self.root), client="test", advisor_config=self.config, clock=lambda: self.now)
        self.service.context = AsyncMock(side_effect=lambda r: {**build_context(r, []), "sources": []})
        self.service.advisor_workflow.task_evidence.install(corpus())

    async def prepare(self, **kwargs):
        return await self.service.prepare_routing([PACKET], available=AVAILABLE, portable=True,
            advisor_route={"model": "economy", "effort": "low", "selection_basis": {"source": "caller", "reason_code": "bounded_ranking"}}, **kwargs)

    async def test_snapshot_privacy_history_cost_and_external_projection(self):
        reply = await self.prepare(task_queries={"fix": "cache invalidation PRIVATE-SENTINEL"})
        self.assertEqual(reply["status"], "awaiting_native_advice")
        serialized = json.dumps(reply)
        self.assertNotIn("PRIVATE-SENTINEL", serialized)
        snap = reply["envelope"]["payload"]["snapshot"]
        validate_routing_snapshot(snap)
        summary = snap["evidence"]["task_similarity_evidence"]
        self.assertEqual(summary["status"], "available")
        ext = _external_state(snap)["evidence"]["task_similarity_evidence"]["packets"][0]
        self.assertNotIn("local", ext)
        self.assertNotIn("comparison", ext)
        self.assertNotIn("local", ext["unknown_current_candidates"])
        # Finish through the existing policy fallback to create an ordinary receipt.
        workflow = self.service.advisor_workflow
        workflow._finish(workflow._states[reply["decision_id"]], reason="advisor_disabled")
        receipt = {"status": "completed", "execution_ref": "chain1", "observed": {"model": "economy", "effort": "low"},
                   "outcome": "accepted", "outcome_basis": "tests", "evidence_refs": ["test-run-1"], "cost_observation": cost_chain()}
        self.service.record_routing_outcome(reply["decision_id"], receipt)
        local = workflow.task_evidence.summarize([PACKET], CANDIDATES)["packets"][0]["local"][0]["groups"][0]
        self.assertEqual(local["expected_cost"]["api_usd"]["mean"], 10)
        self.assertEqual(local["quality"]["mean"], 1)
        self.assertNotIn("PRIVATE-SENTINEL", "".join(p.read_text() for p in self.root.rglob("*.json")))
        with self.assertRaisesRegex(EvidenceError, "opt-in"):
            self.service.record_routing_outcome(reply["decision_id"], {**receipt, "task_description": "private"})
        self.now += 31 * 86400
        self.assertEqual(workflow.task_evidence.summarize([PACKET], CANDIDATES)["packets"][0]["unknown_current_candidates"]["local"], "all")

    async def test_evidence_only_and_old_workflow_when_disabled(self):
        response = await self.service.get_routing_context(["implementation"], available=AVAILABLE, task_query="cache invalidation")
        self.assertEqual(response["task_similarity_evidence"]["packets"][0]["neighbors"], 1)
        self.service.advisor_workflow.task_evidence.config["enabled"] = False
        reply = await self.prepare(task_queries={"fix": "private"})
        self.assertNotIn("task_similarity_evidence", reply["envelope"]["payload"]["snapshot"]["evidence"])

    async def test_description_opt_in_and_targeted_purge(self):
        workflow = self.service.advisor_workflow
        workflow.history.retain_descriptions = True
        reply = await self.prepare()
        workflow._finish(workflow._states[reply["decision_id"]], reason="advisor_disabled")
        self.service.record_routing_outcome(reply["decision_id"], {"status": "completed", "execution_ref": "retained",
            "cost_observation": cost_chain(), "task_description": "PRIVATE-DESCRIPTION"})
        self.assertIn("PRIVATE-DESCRIPTION", "".join(p.read_text() for p in workflow.history.root.glob("*.json")))
        self.assertEqual(workflow.task_evidence.purge_descriptions()["records"], 1)
        self.assertNotIn("PRIVATE-DESCRIPTION", "".join(p.read_text() for p in workflow.history.root.glob("*.json")))
        self.assertIsNotNone(workflow.task_evidence.load())

    async def test_deadline_and_cancellation_release_local_process_scope(self):
        evidence = self.service.advisor_workflow.task_evidence
        evidence.config["deadline_seconds"] = .001
        reply = await evidence.async_summarize([PACKET], CANDIDATES)
        self.assertEqual(reply["status"], "unavailable")
        started, stopped = threading.Event(), threading.Event()
        class Scope:
            def __init__(self, seconds): pass
            def run(self, *args):
                started.set()
                stopped.wait(2)
                return b'{}'
            def cancel(self): stopped.set()
        with patch("route_evidence.processes.ProcessScope", Scope):
            task = asyncio.create_task(evidence.async_summarize([PACKET], CANDIDATES))
            await asyncio.to_thread(started.wait, 1)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
            self.assertTrue(stopped.is_set())


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_fresh_stdio_local_evidence_and_disabled_rollback(self):
        try:
            version = importlib.metadata.version("mcp")
        except importlib.metadata.PackageNotFoundError:
            self.skipTest("optional pinned MCP SDK not installed")
        if version != "2.2.0":
            self.skipTest("requires pinned MCP SDK 2.2.0")
        from mcp import Client, StdioServerParameters
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            TaskEvidence(root).install(corpus())
            config = root / "config.json"
            for enabled in (True, False):
                config.write_text(json.dumps({"schema_version": 2, "client": "test", "task_evidence": {"enabled": enabled}}))
                params = StdioServerParameters(command=sys.executable, args=["-B", str(SCRIPTS / "benchmark_mcp.py"),
                    "--cache-dir", str(root), "--config", str(config), "--offline"])
                async with asyncio.timeout(15), Client(params) as client:
                    reply = await client.call_tool("get_routing_context", {"task_types": ["implementation"],
                        "available": AVAILABLE, "task_query": "cache invalidation PRIVATE-SENTINEL"})
                    self.assertFalse(reply.is_error)
                    result = reply.structured_content
                    self.assertNotIn("PRIVATE-SENTINEL", json.dumps(result))
                    self.assertEqual(result["task_similarity_evidence"]["status"], "available" if enabled else "disabled")
                    prepared = await client.call_tool("prepare_routing", {"packets": [PACKET],
                        "task_queries": {"fix": "cache invalidation PRIVATE-SENTINEL"},
                        "cost_objectives": {"fix": {"unit": "quota_units", "unit_basis": "window-v1", "overhead": None}}})
                    self.assertFalse(prepared.is_error)
                    self.assertEqual(prepared.structured_content["status"], "diagnostic_only")
                    self.assertNotIn("PRIVATE-SENTINEL", json.dumps(prepared.structured_content))
