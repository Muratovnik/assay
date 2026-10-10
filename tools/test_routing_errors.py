"""Regression replay of rejected bootstrap, correctable advice and full history."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import AsyncMock

import test_routing_service as services
import test_routing_decisions as decisions
from route_evidence.advisors.jev import AdapterError, JevAdapter
from route_evidence.core import EvidenceError
from route_evidence.history import _redacted_json


class RoutingErrorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fixture = services.AdvisorServiceTests("runTest")
        self.fixture.setUp()
        self.addCleanup(self.fixture.temp.cleanup)
        self.packets = decisions.packets(4)
        goals = ["Review journal rollback ownership", "Review stale frontend responses",
                 "Check frontend dependency compatibility", "Check Python lock and generator consistency"]
        for packet, goal in zip(self.packets, goals):
            packet["task_spec"]["goal"] = goal
            packet["baseline"] = {"model": "model-01", "effort": "low"}
        self.available = [{"model": "model-00", "efforts": ["low"]},
                          {"model": "model-01", "efforts": ["low"]}]
        self.service = self.fixture.make_service(config={"schema_version": 4,
            "task_evidence": {"enabled": False, "retain_descriptions": True},
            "telemetry": {"mode": "full", "dataset": "smoke"}})

    async def prepare(self, **changes):
        return await self.service.prepare_routing(changes.pop("packets", self.packets),
            available=self.available, advisor_route=changes.pop("advisor_route", decisions.ROUTE),
            portable=True, **changes)

    async def test_original_extra_reason_rejected_before_acquisition_or_decision(self):
        route = copy.deepcopy(decisions.ROUTE)
        route["selection_basis"]["reason"] = "Bounded assessment of four review packets"
        with self.assertRaisesRegex(EvidenceError, "native_selection_basis_invalid: advisor_route.selection_basis"):
            await self.prepare(advisor_route=route)
        self.service.context.assert_not_called()
        self.assertEqual(len(self.service.advisor_workflow._states), 0)
        self.assertEqual(self.service.advisor_workflow._cache, {})
        prepared = await self.prepare()
        self.assertEqual(prepared["status"], "awaiting_native_advice")
        self.assertEqual(prepared["handoff"]["requested_model"], decisions.ROUTE["model"])
        self.assertEqual(len(prepared["envelope"]["payload"]["snapshot"]["packets"]), 4)

    async def test_unavailable_advisor_does_not_select_or_cache_a_baseline(self):
        with self.assertRaisesRegex(EvidenceError, "native_advisor_route_unavailable"):
            await self.prepare(advisor_route={**decisions.ROUTE, "model": "absent-model"})
        self.service.context.assert_awaited_once()
        self.assertEqual(self.service.advisor_workflow.status()["pending"], 0)
        self.assertTrue(all("response" not in state for state in self.service.advisor_workflow._states.values()))
        self.assertEqual(self.service.advisor_workflow._cache, {})

    def test_cli_reports_original_bootstrap_error_with_nonzero_exit(self):
        route = copy.deepcopy(decisions.ROUTE)
        route["selection_basis"]["reason"] = "Bounded assessment"
        root = Path(self.fixture.temp.name)
        config = root / "config.json"
        config.write_text(json.dumps({"schema_version": 4, "telemetry": {"mode": "full"},
            "task_evidence": {"enabled": False}}), encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", str(services.SCRIPTS / "benchmark_router.py"),
            "--config", str(config), "--cache-dir", str(root / "cli-cache"), "prepare", "--request", "-"],
            input=json.dumps({"packets": self.packets, "available": self.available, "advisor_route": route}),
            text=True, capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("native_selection_basis_invalid", result.stderr + result.stdout)
        self.assertNotIn('"selected": {', result.stdout)

    async def test_missing_bootstrap_and_task_details_never_select_four_baselines(self):
        missing = await self.prepare(advisor_route=None)
        self.assertEqual(missing["status"], "needs_advisor_route")
        self.assertTrue(all(d["selected"] is None for d in missing["decisions"]))
        packets = copy.deepcopy(self.packets)
        for packet in packets:
            packet.pop("task_spec")
        missing = await self.prepare(packets=packets)
        self.assertEqual(missing["status"], "needs_task_details")
        self.assertTrue(all(d["selected"] is None for d in missing["decisions"]))

    async def test_corrected_submission_preserves_expiry_and_four_distinct_tasks_with_multiline_evidence(self):
        prose = "First line\r\nSecond line\n\tIndented evidence"
        context = self.service.context.side_effect
        async def multiline(request):
            value = await context(request)
            value["guidance"] = {"documents": [{"sections": [{"excerpt": prose}]}]}
            return value
        self.service.context.side_effect = multiline
        prepared = await self.prepare()
        snapshot = prepared["envelope"]["payload"]["snapshot"]
        answer = decisions.answer(snapshot)
        malformed = copy.deepcopy(answer)
        malformed["answers"].pop()
        with self.assertRaisesRegex(EvidenceError, "invalid_advisor_result.*correct advisor_result"):
            self.service.complete_routing(prepared["decision_id"], malformed)
        self.assertIsNone(self.service.advisor_workflow.history.read(prepared["decision_id"]))
        self.assertEqual(self.service.advisor_workflow._cache, {})
        self.fixture.now += 1
        result = self.service.complete_routing(prepared["decision_id"], answer)
        self.assertEqual(result["status"], "decided")
        self.assertEqual(result["expires_at"], prepared["expires_at"])
        self.assertNotIn("telemetry_status", result)
        record = self.service.advisor_workflow.history.read(prepared["decision_id"])
        self.assertEqual([p["task_spec"]["goal"] for p in record["snapshot"]["packets"]],
                         [p["task_spec"]["goal"] for p in self.packets])
        self.assertEqual(record["full"]["snapshot"]["evidence"]["guidance"]["documents"][0]["sections"][0]["excerpt"], prose)
        self.assertEqual(result, self.service.complete_routing(prepared["decision_id"], answer))
        self.service.context.assert_awaited_once()

    def test_evidence_multiline_permission_does_not_expand_other_history_boundaries(self):
        for text in ("text\x00hidden", "text\x1bcontrol"):
            with self.subTest(text=repr(text)), self.assertRaisesRegex(EvidenceError, "control characters"):
                _redacted_json({"evidence": {"guidance": {"excerpt": text}}}, "snapshot")
        for value in ({"packets": [{"task_spec": {"goal": "line one\nline two"}}]},
                      {"evidence": {"source_id": "line one\nline two"}},
                      {"evidence": {"prompt": "forbidden"}}, {"evidence": {"output": "forbidden"}}):
            with self.subTest(value=value), self.assertRaises(EvidenceError):
                _redacted_json(value, "snapshot")

    async def test_hosted_operational_failures_fallback_but_contract_and_configuration_errors_raise(self):
        for code, fallback in (("jev_timeout", True), ("jev_rate_limited", True),
                               ("jev_invalid_choice_response", False), ("jev_authentication_failed", False),
                               ("jev_external_consent_required", False), ("jev_unknown_failure", False)):
            with self.subTest(code=code):
                service = self.fixture.make_service(config={"schema_version": 3,
                    "advisor": {"enabled": True, "backend": "jev"}, "telemetry": {"mode": "off"}})
                adapter = JevAdapter(service.advisor_workflow.advisor["jev"])
                adapter.recommend = AsyncMock(side_effect=AdapterError(code))
                service.advisor_workflow._jev = adapter
                packets = [{**services.PACKETS[0], "baseline": {"model": "worker-alpha", "effort": "low"}}]
                if fallback:
                    result = await self.fixture.prepare(service, packets=packets)
                    self.assertEqual(result["status"], "decided")
                    self.assertEqual(result["decisions"][0]["reason_codes"], [code, "caller_baseline"])
                else:
                    with self.assertRaisesRegex(EvidenceError, code):
                        await self.fixture.prepare(service, packets=packets)
                self.assertEqual(service.advisor_workflow._cache, {})


if __name__ == "__main__":
    unittest.main()
