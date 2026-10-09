"""Fixed decisions need no acquisition; evidence-sensitive decisions still do."""
from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

import test_routing_service as fixtures

AVAILABLE, PACKETS = fixtures.AVAILABLE, fixtures.PACKETS


class FixedRoutingTests(unittest.IsolatedAsyncioTestCase):
    setUp = fixtures.AdvisorServiceTests.setUp
    make_service = fixtures.AdvisorServiceTests.make_service
    prepare = fixtures.AdvisorServiceTests.prepare

    async def test_fixed_route_does_not_acquire_sources(self):
        for packets, available, decision_type in (
            ([{**PACKETS[0], "explicit_source": "user",
               "explicit": {"model": "worker-alpha", "effort": "high"}}], AVAILABLE, "explicit_user_choice"),
            (PACKETS, [{"model": "worker-alpha", "efforts": ["low"]}], "single_eligible"),
            ([{**PACKETS[0], "explicit_source": "user", "explicit": {"model": "worker-beta"}}],
             AVAILABLE, "single_eligible"),
        ):
            with self.subTest(decision_type=decision_type):
                service = self.make_service()
                with patch("route_evidence.advisors.native.prepare_native", side_effect=AssertionError("unexpected advice")):
                    reply = await self.prepare(service, packets=packets, available=available)
                self.assertEqual(reply["decisions"][0]["decision_type"], decision_type)
                self.assertEqual(reply["evidence_acquisition"], "not_required")
                service.context.assert_not_awaited()

    async def test_unresolved_effort_keeps_advice_and_acquisition(self):
        reply = await self.prepare(packets=[{**PACKETS[0], "explicit_source": "user",
                                             "explicit": {"model": "worker-alpha"}}])
        self.assertEqual(reply["status"], "awaiting_native_advice")
        self.service.context.assert_awaited_once()

    async def test_enabled_task_evidence_does_not_provision_a_fixed_route(self):
        service = self.make_service(config={"schema_version": 2, "telemetry": {"mode": "off"},
                                             "task_evidence": {"enabled": True}})
        evidence = service.advisor_workflow.task_evidence
        with patch.object(evidence.provisioner, "ensure", side_effect=AssertionError("unexpected provisioning")), \
                patch.object(evidence, "load", side_effect=AssertionError("unexpected corpus read")):
            reply = await self.prepare(service, packets=[{**PACKETS[0], "explicit_source": "user",
                                                         "explicit": {"model": "worker-alpha", "effort": "high"}}])
        self.assertEqual(reply["status"], "decided")
        self.assertEqual(reply["evidence_acquisition"], "not_required")
        service.context.assert_not_awaited()

    async def test_numeric_limits_keep_acquisition_for_fixed_choices(self):
        packet = {**PACKETS[0], "explicit_source": "user",
                  "explicit": {"model": "worker-alpha", "effort": "high"}}
        for global_limit in (False, True):
            with self.subTest(global_limit=global_limit):
                service = self.make_service()
                constrained = copy.deepcopy(packet)
                args = {}
                if global_limit:
                    args["constraints"] = {"max_cost_usd": 1}
                else:
                    constrained["requirements"] = {"constraints": {"min_score": .8}}
                await self.prepare(service, packets=[constrained], **args)
                service.context.assert_awaited_once()

    async def test_capability_exclusions_are_enforced_without_acquisition(self):
        packet = {**PACKETS[0], "requirements": {"capabilities": ["shell"]}}
        reply = await self.prepare(packets=[packet])
        self.assertEqual(reply["status"], "no_decision")
        self.assertIsNone(reply["decisions"][0]["selected"])
        self.service.context.assert_not_awaited()

    async def test_fixed_choice_does_not_compete_for_advisor_capacity(self):
        service = self.make_service(config={"schema_version": 2, "advisor": {"max_pending": 1},
                                             "telemetry": {"mode": "off"}})
        self.assertEqual((await self.prepare(service))["status"], "awaiting_native_advice")
        reply = await self.prepare(service, packets=[{**PACKETS[0], "explicit_source": "user",
                                                       "explicit": {"model": "worker-beta", "effort": "medium"}}])
        self.assertEqual(reply["status"], "decided")
        self.assertEqual(service.advisor_workflow.status()["pending"], 1)
        service.context.assert_awaited_once()

    async def test_explicit_refresh_and_offline_replay_keep_the_evidence_path(self):
        for offline in (False, True):
            with self.subTest(offline=offline):
                service = self.make_service(offline=offline)
                service.force = not offline
                reply = await self.prepare(service, available=[{"model": "worker-alpha", "efforts": ["low"]}])
                service.context.assert_awaited_once()
                self.assertNotIn("evidence_acquisition", reply)
                self.assertEqual(reply["usage"], "diagnostic_only" if offline else "routing")


if __name__ == "__main__":
    unittest.main()
