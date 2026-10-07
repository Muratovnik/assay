"""Recommendation defaults and accountable caller exceptions; no model calls."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

from test_routing_decisions import context, packets, answer, ROUTE
from route_evidence.cache import Cache
from route_evidence.core import EvidenceError, digest
from route_evidence.service import RoutingService
from route_evidence.advice import build_snapshot, decide
from route_evidence.advice_contracts import DECISION_POLICY
from route_evidence.history import HistoryStore, replay


AVAILABLE = [{"model": "model-00", "efforts": ["low"]},
             {"model": "model-01", "efforts": ["low"]}]
CHOICE = {"model": "model-01", "effort": "low"}
JUSTIFICATION = {"kind": "justification",
                 "reason": "The task requires a capability missing from the recommended route, verified by the local capability check.",
                 "reference": "capability-check-1"}
CONFIRMATION = {"kind": "user_confirmation", "reference": "user-message-42"}


class CallerOverrideTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.now = 1800000000.0
        self.service = RoutingService(Cache(Path(self.tmp.name), clock=lambda: self.now),
            client="test-client", clock=lambda: self.now,
            advisor_config={"schema_version": 4, "telemetry": {"mode": "metadata"},
                            "task_evidence": {"enabled": False, "auto_download": False}})
        self.service.context = AsyncMock(return_value=context())

    async def prepare(self, task_packets):
        return await self.service.prepare_routing(task_packets, available=AVAILABLE, advisor_route=ROUTE)

    async def test_unexplained_batch_cannot_bypass_recommendation_or_write_state(self):
        tasks = [{"packet_id": name, "task_types": ["implementation"], "features": {},
                  "explicit": CHOICE, "explicit_source": "caller"}
                 for name in ("catalogs", "runtime", "docs", "new-ui", "new-content", "utility-audit")]
        with self.assertRaisesRegex(EvidenceError, "caller_override_required"):
            await self.prepare(tasks)
        self.service.context.assert_not_called()
        self.assertFalse(self.service.advisor_workflow._states)
        self.assertFalse(list(Path(self.tmp.name).rglob("decision-*.json")))

    async def test_omitted_source_and_partial_choice_do_not_evade_exception_guard(self):
        for explicit in (CHOICE, {"model": "model-01"}, {"effort": "low"}):
            for source in (None, "caller"):
                with self.subTest(explicit=explicit, source=source):
                    task = {**packets()[0], "explicit": explicit}
                    if source is not None:
                        task["explicit_source"] = source
                    with self.assertRaisesRegex(EvidenceError, "caller_override_required"):
                        await self.prepare([task])
        self.service.context.assert_not_called()

    async def test_default_recommendation_uses_adequacy_then_measured_cost(self):
        tasks = [{**packets()[0], "baseline": CHOICE}]
        prepared = await self.prepare(tasks)
        self.assertEqual(prepared["status"], "awaiting_native_advice")
        snap = self.service.advisor_workflow._states[prepared["decision_id"]]["snapshot"]
        self.assertEqual(len(snap["packets"][0]["eligible"]), 2)
        completed = self.service.complete_routing(prepared["decision_id"], answer(snap))
        self.assertEqual(completed["decisions"][0]["decision_type"], "advisor")
        self.assertEqual(completed["decisions"][0]["selected"]["model"], "model-00")

    async def test_justified_and_confirmed_exceptions_are_visible_and_private(self):
        for basis in (JUSTIFICATION, CONFIRMATION):
            with self.subTest(kind=basis["kind"]):
                task = {**packets()[0], "explicit": CHOICE, "explicit_source": "caller",
                        "caller_override": basis}
                prepared = await self.prepare([task])
                decision = prepared["decisions"][0]
                self.assertEqual(decision["decision_type"], "caller_choice")
                self.assertEqual(decision["selected"]["model"], "model-01")
                self.assertEqual(decision["selection_provenance"]["caller_override"], basis)
                self.assertEqual(decision["selection_provenance"]["verification"], "declared_not_attested")
                self.assertNotIn("handoff", prepared)
                record = self.service.advisor_workflow.history.read(prepared["decision_id"])
                summary = record["decisions"][0]["selection_provenance"]["caller_override"]
                self.assertEqual(summary, {"kind": basis["kind"], "basis_hash": digest(basis),
                                           "reference": basis["reference"]})
                self.assertNotIn(JUSTIFICATION["reason"], json.dumps(record))

    async def test_invalid_exception_evidence_is_rejected_before_advisor(self):
        invalid = ({}, {"kind": "justification"}, {"kind": "justification", "reason": "   "},
                   {"kind": "justification", "reason": None}, {"kind": "justification", "reason": []},
                   {"kind": "justification", "reason": "\u044f" * 501},
                   {"kind": "justification", "reason": "x" * 1001},
                   {"kind": "justification", "reason": "private password=abcdef"},
                   {"kind": "user_confirmation"}, {"kind": "user_confirmation", "reference": " "},
                   {"kind": "user_confirmation", "reference": "message", "approved": True},
                   {"kind": "unknown", "reason": "unsupported origin"})
        for basis in invalid:
            with self.subTest(basis=basis):
                with self.assertRaisesRegex(EvidenceError, "caller_override"):
                    await self.prepare([{**packets()[0], "explicit": CHOICE, "explicit_source": "caller",
                                         "caller_override": basis}])
        self.service.context.assert_not_called()

    async def test_exception_cannot_be_attached_to_another_origin_or_no_choice(self):
        for task in (packets()[0], {**packets()[0], "explicit": CHOICE, "explicit_source": "user"},
                     {**packets()[0], "explicit": CHOICE, "explicit_source": "configuration"}):
            with self.subTest(task=task):
                with self.assertRaisesRegex(EvidenceError, "caller_override"):
                    await self.prepare([{**task, "caller_override": JUSTIFICATION}])

    async def test_partial_exception_retains_basis_and_hard_constraints(self):
        prepared = await self.prepare([{**packets()[0], "explicit": {"model": "model-01"},
                                        "explicit_source": "caller", "caller_override": JUSTIFICATION}])
        self.assertEqual(prepared["decisions"][0]["selected"]["model"], "model-01")
        self.assertEqual(prepared["decisions"][0]["selection_provenance"]["caller_override"], JUSTIFICATION)
        rejected = await self.prepare([{**packets()[0], "explicit": CHOICE,
            "explicit_source": "caller", "caller_override": JUSTIFICATION,
            "requirements": {"delegation_allowed": False}}])
        self.assertIsNone(rejected["decisions"][0]["selected"])

    def test_full_exception_history_requires_opt_in_and_keeps_replay_basis(self):
        task = {**packets()[0], "explicit": CHOICE, "explicit_source": "caller", "caller_override": JUSTIFICATION}
        snap = build_snapshot(context(), [task], policy=DECISION_POLICY, client="test-client",
                              created_at="2030-01-01T00:00:00Z", expires_at="2030-01-01T00:10:00Z")
        store = HistoryStore(Path(self.tmp.name) / "full", mode="full", clock=lambda: self.now)
        record = store.write_decision("not-retained", snap, None, decide(snap))
        self.assertNotIn("full", record)
        self.assertNotIn(JUSTIFICATION["reason"], json.dumps(record))
        store.retain_descriptions = True
        retained = store.write_decision("retained", snap, None, decide(snap))
        result = replay(retained, policy=DECISION_POLICY)
        self.assertEqual(result["decisions"][0]["selection_provenance"]["caller_override"], JUSTIFICATION)
        self.assertFalse(result["execution_authorized"])

    async def test_actual_user_choice_stays_binding_without_caller_exception(self):
        prepared = await self.prepare([{**packets()[0], "explicit": CHOICE, "explicit_source": "user"}])
        self.assertEqual(prepared["decisions"][0]["decision_type"], "explicit_user_choice")
        self.assertEqual(prepared["decisions"][0]["selected"]["model"], "model-01")

    def test_historical_caller_snapshot_still_replays_without_new_authority(self):
        snap = build_snapshot(context(), [{**packets()[0], "explicit": CHOICE, "explicit_source": "caller"}],
            policy=DECISION_POLICY, client="test-client", created_at="2030-01-01T00:00:00Z",
            expires_at="2030-01-01T00:10:00Z")
        store = HistoryStore(Path(self.tmp.name) / "history", mode="full", clock=lambda: self.now)
        store.retain_descriptions = True
        record = store.write_decision("historical-caller", snap, None, decide(snap))
        result = replay(record)
        self.assertEqual(result["decisions"][0]["decision_type"], "caller_choice")
        self.assertFalse(result["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
