"""Application lifecycle contracts with synthetic evidence and no model calls."""
from __future__ import annotations

import asyncio
import copy
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "route-subagents" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from route_evidence.advisor_config import migrate_config, settings
from route_evidence.cache import Cache
from route_evidence.core import EvidenceError, timestamp
from route_evidence.routing import build_context
from route_evidence.service import RoutingService, load_config

AVAILABLE = [{"model": "worker-alpha", "efforts": ["low", "high"]},
             {"model": "worker-beta", "efforts": ["medium"]}]
ROUTE = {"model": "worker-beta", "effort": "medium",
         "selection_basis": {"source": "caller", "reason_code": "bounded_ranking"}}
PACKETS = [{"packet_id": "implementation", "task_types": ["implementation"], "features": {}}]


class AdvisorServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = 1800000000.0
        self.config = {"schema_version": 2, "telemetry": {"mode": "off"}}
        self.service = self.make_service()

    def make_service(self, *, offline=False, config=None):
        service = RoutingService(Cache(Path(self.temp.name) / "cache", clock=lambda: self.now),
            client="test-client", clock=lambda: self.now, offline=offline, advisor_config=config or self.config)
        async def context(request):
            return {**build_context(request, []), "sources": [], "data_status": "unavailable",
                    "data_message": "synthetic missing evidence", "usage": "diagnostic_only" if offline else "routing"}
        service.context = AsyncMock(side_effect=context)
        return service

    async def prepare(self, service=None, **changes):
        return await (service or self.service).prepare_routing(
            changes.pop("packets", PACKETS), available=changes.pop("available", AVAILABLE),
            advisor_route=changes.pop("advisor_route", ROUTE), **changes)

    def answer(self, reply, service=None):
        workflow = (service or self.service).advisor_workflow
        snap = workflow._states[reply["decision_id"]]["snapshot"]
        return {"schema_version": 1, "snapshot_id": snap["snapshot_id"], "backend": "native-economy",
                "requested_model": ROUTE["model"], "resolved_model": ROUTE["model"], "effort": ROUTE["effort"],
                "rankings": [{"packet_id": p["packet_id"], "ranking": list(p["eligible"]),
                              "abstained": False, "reason_codes": [], "probabilities": None, "confidence": None}
                             for p in snap["packets"]], "metadata": {}}

    async def test_prepare_complete_and_idempotence(self):
        prepared = await self.prepare()
        self.assertEqual(prepared["status"], "awaiting_native_advice")
        self.service.context.assert_awaited_once()
        answer = self.answer(prepared)
        result = self.service.complete_routing(prepared["decision_id"], answer)
        self.assertEqual(result["status"], "decided")
        self.assertFalse(result["launch_verified"])
        self.assertEqual(result, self.service.complete_routing(prepared["decision_id"], answer))
        conflict = copy.deepcopy(answer)
        conflict["rankings"][0]["ranking"].reverse()
        with self.assertRaisesRegex(EvidenceError, "conflicting"):
            self.service.complete_routing(prepared["decision_id"], conflict)

    async def test_bootstrap_missing_and_disabled_never_call_provider(self):
        missing = await self.prepare(advisor_route=None)
        self.assertEqual(missing["status"], "needs_advisor_route")
        legacy = self.make_service(config={"schema_version": 1})
        disabled = await self.prepare(legacy)
        self.assertEqual(disabled["status"], "no_decision")
        self.assertFalse(legacy.advisor_workflow.advisor["enabled"])

    async def test_explicit_choice_and_single_candidate_bypass_native(self):
        with patch("route_evidence.advisors.native.prepare_native", side_effect=AssertionError("unexpected advisor")):
            explicit = await self.prepare(packets=[{**PACKETS[0], "explicit": {"model": "worker-alpha", "effort": "high"}}])
            self.assertEqual(explicit["decisions"][0]["decision_type"], "explicit_user_choice")
            one = await self.prepare(available=[{"model": "worker-alpha", "efforts": ["low"]}])
            self.assertEqual(one["decisions"][0]["decision_type"], "single_eligible")

    async def test_offline_forbids_any_adapter_and_outcome_write(self):
        offline = self.make_service(offline=True)
        with patch("route_evidence.advisors.native.prepare_native", side_effect=AssertionError("unexpected advisor")):
            reply = await self.prepare(offline)
        self.assertEqual(reply["usage"], "diagnostic_only")
        self.assertNotIn("handoff", reply)
        self.assertFalse(offline.record_routing_outcome(reply["decision_id"], {})["recorded"])

    async def test_pending_bound_expiry_and_inventory_change(self):
        limited = self.make_service(config={"schema_version": 2, "advisor": {"max_pending": 1}, "telemetry": {"mode": "off"}})
        prepared = await self.prepare(limited)
        self.assertEqual((await self.prepare(limited))["status"], "busy")
        self.now += 601
        self.assertEqual(limited.complete_routing(prepared["decision_id"], self.answer(prepared, limited))["status"], "expired")
        self.assertEqual((await self.prepare(limited))["status"], "awaiting_native_advice")
        initial = await self.prepare()
        self.service.prepare(["implementation"], available=[{"model": "changed", "efforts": ["low"]}])
        result = self.service.complete_routing(initial["decision_id"], self.answer(initial))
        self.assertEqual(result["status"], "no_decision")

    async def test_exact_cache_reuses_only_unchanged_semantics(self):
        first = await self.prepare()
        self.service.complete_routing(first["decision_id"], self.answer(first))
        hit = await self.prepare()
        self.assertTrue(hit["cache_hit"])
        self.assertNotEqual(first["decision_id"], hit["decision_id"])
        renamed = await self.prepare(packets=[{**PACKETS[0], "packet_id": "same-work-new-id"}])
        self.assertTrue(renamed["cache_hit"])
        self.assertEqual(renamed["decisions"][0]["packet_id"], "same-work-new-id")
        different = await self.prepare(packets=[{"packet_id": "tests", "task_types": ["tests"], "features": {}}])
        self.assertEqual(different["status"], "awaiting_native_advice")

    async def test_invalid_native_response_does_not_choose_parent(self):
        prepared = await self.prepare()
        answer = self.answer(prepared)
        answer["rankings"][0]["ranking"].pop()
        result = self.service.complete_routing(prepared["decision_id"], answer)
        self.assertEqual(result["status"], "no_decision")
        self.assertIsNone(result["decisions"][0]["selected"])

    async def test_portable_envelope_restarts_without_model_calls(self):
        prepared = await self.prepare(portable=True)
        answer = self.answer(prepared)
        restarted = self.make_service()
        result = restarted.complete_routing(prepared["decision_id"], answer, envelope=prepared["envelope"])
        self.assertEqual(result["status"], "decided")
        restarted.context.assert_not_called()
        envelope = copy.deepcopy(prepared["envelope"])
        envelope["payload"]["snapshot"]["client"] = "other-client"
        with self.assertRaises(EvidenceError):
            self.make_service().complete_routing(prepared["decision_id"], answer, envelope=envelope)

    async def test_cancellation_does_not_leave_pending_slot(self):
        self.service.context = AsyncMock(side_effect=asyncio.CancelledError)
        with self.assertRaises(asyncio.CancelledError):
            await self.prepare()
        self.assertEqual(self.service.advisor_workflow.status()["pending"], 0)

    async def test_cli_portable_completion_needs_no_network_or_model(self):
        self.now = time.time()
        prepared = await self.prepare(portable=True)
        root = Path(self.temp.name)
        config = root / "config.json"
        config.write_text(json.dumps({**self.config, "client": "test-client"}), encoding="utf-8")
        document = {"decision_id": prepared["decision_id"], "advisor_result": self.answer(prepared),
                    "envelope": prepared["envelope"]}
        process = subprocess.run([sys.executable, "-B", str(SCRIPTS / "benchmark_router.py"),
            "--config", str(config), "--cache-dir", str(root / "cli-cache"), "complete", "--request", "-"],
            input=json.dumps(document), text=True, capture_output=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
        self.assertEqual(json.loads(process.stdout)["status"], "decided")

    async def test_metadata_and_full_records_are_usable_through_service(self):
        from route_evidence.history import replay
        for mode in ("metadata", "full"):
            service = self.make_service(config={"schema_version": 2, "telemetry": {"mode": mode}})
            prepared = await self.prepare(service)
            result = service.complete_routing(prepared["decision_id"], self.answer(prepared, service))
            self.assertNotIn("telemetry_status", result)
            record = service.advisor_workflow.history.read(prepared["decision_id"])
            self.assertIsNotNone(record)
            diagnostic = replay(record)
            self.assertEqual(diagnostic["status"], "replayed" if mode == "full" else "insufficient_record")
            if mode == "full":
                self.assertEqual(diagnostic["decisions"][0]["selected"], result["decisions"][0]["selected"])
                self.assertFalse(diagnostic["execution_authorized"])

    async def test_expired_evidence_cannot_select_even_an_explicit_route(self):
        old_context = self.service.context.side_effect
        async def stale(request):
            context = await old_context(request)
            context["sources"] = [{"source_id": "old", "last_success_at": timestamp(self.now - 90000)}]
            return context
        self.service.context.side_effect = stale
        result = await self.prepare(packets=[{**PACKETS[0], "explicit": {"model": "worker-alpha", "effort": "high"}}])
        self.assertEqual(result["status"], "no_decision")
        self.assertIsNone(result["decisions"][0]["selected"])
        self.assertIn("snapshot_expired", result["decisions"][0]["reason_codes"])


class AdvisorConfigTests(unittest.TestCase):
    def test_v1_migration_is_explicit_exclusive_and_preserves_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "v1.json", Path(tmp) / "v2.json"
            old = {"schema_version": 1, "client": "test", "preferences": {"max_cost_usd": 2},
                   "inventory": {"available": AVAILABLE, "observed_at": timestamp(1800000000)}}
            source.write_text(json.dumps(old), encoding="utf-8")
            original = source.read_bytes()
            migrate_config(source, target, enable_advisor=True)
            migrated = load_config(target)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(migrated["inventory"], old["inventory"])
            self.assertEqual(migrated["preferences"], old["preferences"])
            self.assertEqual(migrated["advisor"]["backend"], "native-economy")
            self.assertFalse(migrated["advisor"]["jev"]["enabled"])
            with self.assertRaises(FileExistsError):
                migrate_config(source, target)

    def test_unknown_config_and_unconsented_endpoint_are_rejected(self):
        for change in ({"advisor": {"model": "fixed-worker"}}, {"telemetry": {"mode": "everything"}},
                       {"advisor": {"jev": {"endpoint": "https://example.invalid"}}},
                       {"advisor": {"max_pending": True}}, {"policy": {"unknown": True}}):
            with self.subTest(change=change), self.assertRaises(EvidenceError):
                settings({"schema_version": 2, **change})


if __name__ == "__main__":
    unittest.main()
