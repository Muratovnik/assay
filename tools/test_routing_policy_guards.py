"""Contract regressions for economic selection and registered native dispatch."""
from __future__ import annotations

import copy
import json
import unittest
from unittest.mock import AsyncMock

import test_routing_decisions as decisions
import test_routing_pipeline as pipeline_fixture
from route_evidence.advice import decide, semantic_projection
from route_evidence.advice_contracts import validate_packets, validate_routing_snapshot
from route_evidence.advisors.jev import _external_state
from route_evidence.advisors.native import parse_native
from route_evidence.core import EvidenceError, encoded
from route_evidence.history import HistoryStore, replay
from route_evidence.pipeline import compact
from route_evidence.pipeline_config import confirm_inventory
from route_evidence.task_costs import compare
from route_evidence.task_evidence import attach_summary, validate_summary


class RequiredDispatchGuards(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.host = self.new_host()

    def new_host(self):
        host = pipeline_fixture.PipelineTests("runTest")
        host.setUp()
        self.addCleanup(host.tmp.cleanup)
        return host

    def authorize(self, decision_id, packet_id, **extra):
        return self.host.pipeline.authorize(self.host.rpc("authorize_routing_launch", {
            "decision_id": decision_id, "packet_id": packet_id, **extra}))

    async def test_provisional_binding_cannot_resume_another_packets_worker(self):
        host = self.host
        host.use_aliases(approved_choices={"p1": {"model": "sonnet", "effort": "low"},
                                           "p2": {"model": "haiku", "effort": "low"}})
        prepared = await host.prepare(
            packets=[{**pipeline_fixture.PACKETS[0], "packet_id": p} for p in ("p1", "p2")],
            launch_requests={p: {"profile": "general-purpose", "prompt": "bounded " + p} for p in ("p1", "p2")})
        decision_id = prepared["decision_id"]
        first, second = (self.authorize(decision_id, p) for p in ("p1", "p2"))
        host.dispatched(first, "c1")
        host.now += 1
        host.dispatched(second, "c2")
        name = first["input"]["subagent_type"]
        self.assertEqual(name, second["input"]["subagent_type"])
        host.event("SubagentStart", agent="agent-2", agent_type=name)
        host.event("SubagentStart", agent="agent-1", agent_type=name)
        host.event("SubagentStop", agent="agent-2", effort={"level": "low"})
        with self.assertRaisesRegex(EvidenceError, "continuation_requires_authoritative_binding"):
            self.authorize(decision_id, "p1", resume_agent_id="agent-2")
        with host.pipeline.store.transaction() as tx:
            self.assertEqual(len(tx.values("attempt")), 2)
        host.returned("c2", "agent-2", "haiku-resolved")
        host.returned("c1", "agent-1", "sonnet-resolved")
        with self.assertRaisesRegex(EvidenceError, "continuation_requires_observed_matching_worker"):
            self.authorize(decision_id, "p1", resume_agent_id="agent-2")
        resumed = self.authorize(decision_id, "p2", resume_agent_id="agent-2")
        self.assertEqual(host.dispatched(resumed, "resume-c2")["model"], "haiku")

    async def test_inventory_removal_invalidates_decision_and_existing_launch(self):
        host = self.host
        host.use_aliases(approved_choices={"work": {"model": "sonnet", "effort": "low"}})
        host.use_inventory_file(copy.deepcopy(host.config["inventory"]["available"]))
        prepared = await host.prepare()
        launch = host.authorize(prepared["decision_id"])
        host.now += 1
        confirm_inventory(host.config, available=[{"model": "haiku", "efforts": ["low"]}], clock=lambda: host.now)
        with self.assertRaisesRegex(EvidenceError, "inventory_changed_reprepare_required"):
            host.authorize(prepared["decision_id"])
        with self.assertRaisesRegex(EvidenceError, "inventory_changed_reprepare_required"):
            host.decision(prepared["decision_id"])
        gate = host.event("PreToolUse", tool_name="Agent", tool_use_id="removed-route", tool_input=launch["input"])
        self.assertEqual(gate["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("inventory_changed_reprepare_required", gate["hookSpecificOutput"]["permissionDecisionReason"])
        again = await host.prepare()
        self.assertIsNone(again["decisions"][0]["selected"])
        self.assertEqual(again["decisions"][0]["reason_codes"], ["invalid_explicit_choice"])

    async def test_confirming_unchanged_inventory_preserves_a_prepared_launch(self):
        host = self.host
        host.config["pipeline"]["approved_choices"] = {"work": pipeline_fixture.BASELINE}
        host.use_inventory_file()
        prepared = await host.prepare()
        host.now += 1
        confirm_inventory(host.config, clock=lambda: host.now)
        launch = host.authorize(prepared["decision_id"])
        self.assertIn("PRIVATE_WORK_PROMPT", host.dispatched(launch, "current-route")["prompt"])

    async def test_late_route_mismatch_invalidates_a_prepared_continuation(self):
        host = self.host
        host.config["pipeline"]["approved_choices"] = {"work": pipeline_fixture.BASELINE}
        host.configure()
        prepared = await host.prepare()
        worker = host.authorize(prepared["decision_id"])
        host.launch(worker, agent="worker-a", tool_id="w")
        host.event("SubagentStop", agent="worker-a", effort={"level": "low"})
        continuation = host.authorize(prepared["decision_id"], resume_agent_id="worker-a")
        host.returned("w", "worker-a", "wrong-model")
        with self.assertRaisesRegex(EvidenceError, "continuation_observed_route_mismatch"):
            host.authorize(prepared["decision_id"], resume_agent_id="worker-a")
        gate = host.event("PreToolUse", tool_name="Agent", tool_use_id="resume-w", tool_input=continuation["input"])
        self.assertEqual(gate["hookSpecificOutput"]["permissionDecision"], "deny")

    async def finished_alias_worker(self, host):
        host.use_aliases(approved_choices={"work": {"model": "sonnet", "effort": "low"}}, inventory_ttl_hours=1)
        host.use_inventory_file(copy.deepcopy(host.config["inventory"]["available"]))
        prepared = await host.prepare()
        worker = host.authorize(prepared["decision_id"])
        host.launch(worker, agent="worker-a", tool_id="original-call")
        host.event("SubagentStop", agent="worker-a", effort={"level": "low"})
        host.returned("original-call", "worker-a", "fixture-sonnet")
        return prepared["decision_id"]

    async def test_withdrawn_model_or_effort_blocks_continuation_authorization(self):
        host = self.host
        decision_id = await self.finished_alias_worker(host)
        for removed in ("model", "effort"):
            with self.subTest(removed=removed):
                available = [{"model": "haiku", "efforts": ["low"]}]
                if removed == "effort":
                    available.append({"model": "sonnet", "efforts": ["high"]})
                host.now += 1
                confirm_inventory(host.config, available=available, clock=lambda: host.now)
                with self.assertRaisesRegex(EvidenceError, "continuation_route_unavailable"):
                    host.authorize(decision_id, resume_agent_id="worker-a")

    async def test_withdrawal_after_authorization_blocks_continuation_dispatch(self):
        host = self.host
        decision_id = await self.finished_alias_worker(host)
        continuation = host.authorize(decision_id, resume_agent_id="worker-a")
        for removed in ("model", "effort"):
            with self.subTest(removed=removed):
                available = [{"model": "haiku", "efforts": ["low"]}]
                if removed == "effort":
                    available.append({"model": "sonnet", "efforts": ["high"]})
                host.now += 1
                confirm_inventory(host.config, available=available, clock=lambda: host.now)
                gate = host.event("PreToolUse", tool_name="Agent", tool_use_id="resume-" + removed,
                                  tool_input=continuation["input"])
                self.assertEqual(gate["hookSpecificOutput"]["permissionDecision"], "deny")
                self.assertIn("continuation_route_unavailable", gate["hookSpecificOutput"]["permissionDecisionReason"])

    async def test_continuation_preserves_unchanged_expired_and_unrelated_inventory_controls(self):
        for change in ("unchanged", "expired", "unrelated"):
            with self.subTest(change=change):
                host = self.host if change == "unchanged" else self.new_host()
                decision_id = await self.finished_alias_worker(host)
                if change == "expired":
                    host.now += 3601
                if change == "unrelated":
                    confirm_inventory(host.config, available=[
                        {"model": "sonnet", "efforts": ["low", "high"], "evidence_names": ["new-benchmark-spelling"]},
                        {"model": "opus", "efforts": ["high"]}], clock=lambda: host.now)
                continuation = host.authorize(decision_id, resume_agent_id="worker-a")
                dispatched = host.dispatched(continuation, "resume-control")
                self.assertEqual(dispatched["resume"], "worker-a")
                self.assertEqual(dispatched["model"], "sonnet")


class AdequacyFallbackGuards(unittest.TestCase):
    def result(self, choices):
        packets = decisions.packets()
        packets[0]["baseline"] = {"model": "model-00", "effort": "low"}
        snapshot = decisions.snapshot(task_packets=packets)
        return decide(snapshot, parse_native(snapshot, decisions.answer(snapshot, choices)))[0]

    def test_a_known_inadequate_baseline_is_never_an_executable_fallback(self):
        for other in ("inadequate", "unknown"):
            with self.subTest(other=other):
                result = self.result({"model-00": "inadequate", "model-01": other})
                self.assertIsNone(result["selected"])
                self.assertEqual(result["status"], "no_decision")
                self.assertEqual(result["fallback"]["reason"], "baseline_task_inadequate")

    def test_unknown_baseline_remains_an_explicitly_qualified_fallback(self):
        result = self.result({"model-00": "unknown", "model-01": "unknown"})
        self.assertEqual(result["selected"]["model"], "model-00")
        self.assertEqual(result["decision_type"], "fallback")
        self.assertIn("task_adequacy_unknown", result["reason_codes"])

    def test_required_result_preserves_qualifications_without_private_assessments(self):
        result = self.result({"model-00": "inadequate", "model-01": "unknown"})
        projected = compact({"status": "no_decision", "decisions": [result]})["decisions"][0]
        self.assertEqual(projected["economic_assessment"]["inadequate_count"], 1)
        self.assertEqual(projected["economic_assessment"]["unknown_count"], 1)
        self.assertEqual(projected["fallback"]["reason"], "baseline_task_inadequate")
        self.assertEqual(projected["selection_provenance"]["verification"], "task_inference_not_attested")
        self.assertNotIn("comparisons", projected["economic_assessment"])
        self.assertNotIn("assessments", projected)


class PairedCostSelectionGuards(unittest.TestCase):
    def observed_pair(self, left, right, costs, *, basis="same-conditions", qualities=(1, 1), unit="api_usd"):
        return [{"task_id": basis + "-" + str(i), "model": model, "effort": "low", "complete": True,
                 "score": quality, "metric": "accepted", "comparison_basis": basis, "cost_scope": "chain",
                 "costs": {unit: cost}, "unit_basis": {unit: "same-tariff"}}
                for i in range(3) for model, cost, quality in zip((left, right), costs, qualities)]

    def selected(self, rows, *, baseline=None, costs=(.2, .5), overhead=.05, choices=None, unit="api_usd", objective=None):
        packets = decisions.packets()
        if baseline:
            packets[0]["baseline"] = {"model": baseline, "effort": "low"}
        if objective:
            packets[0]["cost_objective"] = objective
        context = decisions.context(costs, (.88,) * len(costs), len(costs))
        snapshot = decisions.snapshot(ctx=context, task_packets=packets)
        baseline_id = next((c["candidate_id"] for c in snapshot["candidates"] if c["model"] == baseline), None)
        comparison = compare(rows, snapshot["candidates"], baseline_id, unit, overhead)
        snapshot = attach_summary(snapshot, {"schema_version": 1, "status": "available", "mode": "structured",
            "cost_units_are_not_interchangeable": True,
            "packets": [{"packet_id": "work-0", "comparison": comparison}]})
        return decide(snapshot, parse_native(snapshot, decisions.answer(snapshot, choices)))[0]

    def test_baseline_and_overhead_do_not_reverse_paired_full_chain_preference(self):
        rows = self.observed_pair("model-00", "model-01", (2., .4))
        for baseline in ("model-00", "model-01", None):
            for overhead in (.05, None):
                with self.subTest(baseline=baseline, overhead=overhead):
                    result = self.selected(list(reversed(rows)), baseline=baseline, overhead=overhead)
                    self.assertEqual(result["selected"]["model"], "model-01")
                    self.assertIn("paired_chain_cost_selected", result["reason_codes"])
                    self.assertIn("observational_cost_transfer", result["economic_assessment"]["unknowns"])

    def test_a_local_pair_does_not_promote_its_winner_over_unpaired_alternatives(self):
        rows = self.observed_pair("model-00", "model-01", (2., .4))
        result = self.selected(rows, baseline="model-00", costs=(.2, .5, .1))
        self.assertEqual(result["selected"]["model"], "model-02")
        self.assertIn("uncompared_alternatives", result["economic_assessment"]["unknowns"])
        self.assertIn("benchmark_cost_selected", result["reason_codes"])
        self.assertEqual(result["economic_assessment"]["selection_unit"], "api_usd")

    def test_quota_pairs_do_not_inherit_an_unmeasured_routes_dollar_preference(self):
        rows = self.observed_pair("model-00", "model-01", (2., .4), unit="quota_units")
        result = self.selected(rows, costs=(.2, .5, .1), unit="quota_units")
        self.assertEqual(result["selected"]["model"], "model-01")
        assessment = result["economic_assessment"]
        self.assertEqual(assessment["objective_unit"], "quota_units")
        self.assertEqual(assessment["selection_unit"], "quota_units")
        self.assertEqual(assessment["selection_basis"], "paired_chain_cost")
        self.assertIn("quota_cost_unknown", assessment["unknowns"])
        self.assertIn("uncompared_alternatives", assessment["unknowns"])
        self.assertTrue(assessment["comparisons"])
        projected = compact({"decisions": [result]})["decisions"][0]["economic_assessment"]
        for key in ("objective_unit", "selection_unit", "selection_basis"):
            self.assertEqual(projected[key], assessment[key])
        self.assertNotIn("comparisons", projected)
        self.assertNotIn("local_comparison", projected)

    def test_missing_quota_uses_known_dollars_only_as_an_explicitly_qualified_fallback(self):
        for unit in ("quota_units", "api_usd", None):
            with self.subTest(unit=unit):
                result = self.selected([], costs=(.2, .5, .1), unit=unit)
                self.assertEqual(result["selected"]["model"], "model-02")
                assessment = result["economic_assessment"]
                self.assertEqual(assessment["objective_unit"], unit)
                self.assertEqual(assessment["selection_unit"], "api_usd")
                self.assertEqual(assessment["selection_basis"], "benchmark_cost")
                self.assertEqual("quota_cost_unknown" in assessment["unknowns"], unit == "quota_units")
                self.assertIn("benchmark_cost_selected", result["reason_codes"])
        result = self.selected([], costs=(None, None), unit="quota_units")
        self.assertIsNone(result["economic_assessment"]["selection_unit"])
        self.assertIn("quota_cost_unknown", result["economic_assessment"]["unknowns"])
        self.assertNotIn("benchmark_cost_selected", result["reason_codes"])

    def test_local_measurement_must_match_the_declared_unit_and_basis(self):
        objective = {"unit": "quota_units", "unit_basis": "same-tariff", "overhead": None}
        for unit, basis, expected in (("api_usd", "same-tariff", "model-00"),
                                      ("quota_units", "other-tariff", "model-00"),
                                      ("quota_units", "same-tariff", "model-01")):
            with self.subTest(unit=unit, basis=basis):
                rows = self.observed_pair("model-00", "model-01", (2., .4), unit=unit)
                for row in rows:
                    row["unit_basis"][unit] = basis
                result = self.selected(rows, unit=unit, objective=objective)
                self.assertEqual(result["selected"]["model"], expected)
                self.assertEqual(result["economic_assessment"]["objective_unit"], "quota_units")
                self.assertEqual("quota_cost_unknown" in result["economic_assessment"]["unknowns"], expected == "model-00")

    def test_local_pair_cycles_do_not_fabricate_a_global_cost_winner(self):
        rows = (self.observed_pair("model-00", "model-01", (1., 2.), basis="first")
                + self.observed_pair("model-01", "model-02", (1., 2.), basis="second")
                + self.observed_pair("model-02", "model-00", (1., 2.), basis="third"))
        result = self.selected(rows, costs=(.2, .2, .2))
        self.assertIsNone(result["selected"])
        self.assertIn("cost_cohort_conflict", result["reason_codes"])

    def test_disjoint_local_minima_remain_incomparable(self):
        rows = (self.observed_pair("model-00", "model-01", (1., 2.), basis="first")
                + self.observed_pair("model-02", "model-03", (.5, 2.), basis="second"))
        result = self.selected(rows, costs=(None, None, None, None))
        self.assertIn(result["selected"]["model"], {"model-00", "model-02"})
        self.assertIn("cost_groups_incomparable", result["economic_assessment"]["unknowns"])
        self.assertNotIn("economic_tie", result["reason_codes"])

    def test_paired_quality_regression_is_visible_even_when_both_routes_are_task_adequate(self):
        rows = self.observed_pair("model-00", "model-01", (.4, 2.), qualities=(.5, 1))
        result = self.selected(rows, costs=(None, None))
        self.assertIn("paired_quality_cost_tradeoff", result["economic_assessment"]["unknowns"])
        self.assertIn("economic_uncertainty", result["reason_codes"])
        self.assertNotIn("economic_tie", result["reason_codes"])
        self.assertNotIn("paired_chain_cost_selected", result["reason_codes"])
        self.assertNotIn("benchmark_cost_selected", result["reason_codes"])
        self.assertIn("cost_preference_unknown", result["reason_codes"])

    def test_local_cost_cannot_select_an_inadequate_route(self):
        rows = self.observed_pair("model-00", "model-01", (.4, 2.))
        result = self.selected(rows, choices={"model-00": "inadequate"})
        self.assertEqual(result["selected"]["model"], "model-01")


    def test_equal_chain_cost_prefers_strictly_better_paired_quality_in_either_direction(self):
        for qualities, expected in (((1, .5), "model-00"), ((.5, 1), "model-01")):
            with self.subTest(qualities=qualities):
                rows = self.observed_pair("model-00", "model-01", (1., 1.), qualities=qualities)
                for ordered in (rows, list(reversed(rows))):
                    result = self.selected(ordered)
                    self.assertEqual(result["selected"]["model"], expected)
                    self.assertNotIn("economic_tie", result["reason_codes"])
        result = self.selected(self.observed_pair("model-00", "model-01", (1., 1.)))
        self.assertIn("economic_tie", result["reason_codes"])

    def test_a_surviving_minimum_does_not_hide_an_incomparable_conflicting_component(self):
        context = decisions.context(candidate_count=4)
        first = context["tasks"][0]["primary_comparisons"][0]
        reverse = copy.deepcopy(first)
        reverse["harness"] = "reversed-costs"
        for row, cost in zip(reverse["candidates"], (.8, .1)):
            row["expenses"]["cost_usd"] = cost
        separate = copy.deepcopy(first)
        separate["harness"] = "independent-costs"
        for row, model in zip(separate["candidates"], ("model-02", "model-03")):
            row["model"] = model
        context["tasks"][0]["primary_comparisons"].extend((reverse, separate))
        snapshot = decisions.snapshot(ctx=context)
        result = decide(snapshot, parse_native(snapshot, decisions.answer(snapshot)))[0]
        self.assertEqual(result["selected"]["model"], "model-02")
        self.assertIn("cost_groups_incomparable", result["economic_assessment"]["unknowns"])
        self.assertIn("cost_cohort_conflict", result["economic_assessment"]["unknowns"])
        self.assertIn("economic_uncertainty", result["reason_codes"])
        # A measured bridge establishes a minimum even though the losers' cost
        # ordering differs across cohorts; no unrelated conflict is hidden.
        bridge = copy.deepcopy(first)
        bridge["harness"] = "measured-bridge"
        for row, model, cost in zip(bridge["candidates"], ("model-02", "model-00"), (.1, .4)):
            row.update(model=model, expenses={"cost_usd": cost})
        context["tasks"][0]["primary_comparisons"].append(bridge)
        snapshot = decisions.snapshot(ctx=context)
        result = decide(snapshot, parse_native(snapshot, decisions.answer(snapshot)))[0]
        self.assertEqual(result["selected"]["model"], "model-02")
        self.assertNotIn("cost_groups_incomparable", result["economic_assessment"]["unknowns"])
        self.assertNotIn("cost_cohort_conflict", result["economic_assessment"]["unknowns"])


class AdvisorResultTypeGuards(unittest.TestCase):
    def test_legacy_native_malformed_ids_raise_the_classified_validation_error(self):
        from test_routing_adapters import native_result, routing_snapshot
        snapshot = routing_snapshot()
        valid = native_result(snapshot)
        self.assertEqual(parse_native(snapshot, valid)["schema_version"], 1)
        for key, value in (("packet_id", []), ("ranking", [[], snapshot["packets"][0]["eligible"][1]]),
                           ("ties", [[{}, []]])):
            with self.subTest(key=key):
                malformed = copy.deepcopy(valid)
                malformed["rankings"][0][key] = value
                with self.assertRaises(EvidenceError):
                    parse_native(snapshot, malformed)

    def test_jev_malformed_choice_is_a_safe_adapter_error(self):
        from route_evidence.advisors.jev import AdapterError, _normalize_answer
        packet = {"packet_id": "work", "eligible": ["one", "two"]}
        value = {"choice": "one", "probabilities": {"one": .6, "two": .4, "abstain": 0}, "confidence": .6}
        self.assertEqual(_normalize_answer(packet, value)["ranking"][0], "one")
        with self.assertRaisesRegex(AdapterError, "jev_invalid_choice_response"):
            _normalize_answer(packet, {**value, "choice": []})


class AdvisorFallbackLifecycleGuards(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fixture = decisions.DecisionLifecycleTests("runTest")
        self.fixture.setUp()
        self.addCleanup(self.fixture.tmp.cleanup)

    async def prepare(self, service, *, packets=None, **options):
        packets = packets or decisions.packets()
        packets[0]["baseline"] = {"model": "model-00", "effort": "low"}
        prepared = await service.prepare_routing(packets,
            available=[{"model": "model-00", "efforts": ["low"]}, {"model": "model-01", "efforts": ["low"]}],
            advisor_route=decisions.ROUTE, portable=True, **options)
        self.assertEqual(prepared["status"], "awaiting_native_advice")
        return prepared, prepared["envelope"]["payload"]["snapshot"]

    async def test_valid_inadequacy_result_blocks_the_baseline_through_the_live_workflow(self):
        service = self.fixture.service()
        prepared, snapshot = await self.prepare(service)
        result = service.complete_routing(prepared["decision_id"], decisions.answer(snapshot,
            {"model-00": "inadequate", "model-01": "inadequate"}))
        self.assertEqual(result["status"], "no_decision")
        self.assertIsNone(result["decisions"][0]["selected"])
        self.assertEqual(result["decisions"][0]["fallback"]["reason"], "baseline_task_inadequate")

    async def test_invalid_result_does_not_promote_partial_adequacy_claims_to_facts(self):
        service = self.fixture.service()
        prepared, snapshot = await self.prepare(service)
        malformed = decisions.answer(snapshot, {"model-00": "inadequate", "model-01": "inadequate"})
        malformed["answers"][0]["name"] = []
        result = service.complete_routing(prepared["decision_id"], malformed)
        self.assertIsNone(result["advisor_result"])
        self.assertEqual(result["decisions"][0]["decision_type"], "fallback")
        self.assertEqual(result["decisions"][0]["selected"]["model"], "model-00")
        self.assertIn("invalid_advisor_result", result["decisions"][0]["reason_codes"])
        self.assertNotIn("economic_assessment", result["decisions"][0])

    async def test_malformed_legacy_result_and_valid_abstention_keep_the_eligible_fallback(self):
        self.fixture.config = {"schema_version": 3, "telemetry": {"mode": "off"}}
        service = self.fixture.service()
        prepared, _ = await self.prepare(service)
        malformed = copy.deepcopy(prepared["handoff"]["result_contract"])
        malformed["rankings"][0]["packet_id"] = []
        result = service.complete_routing(prepared["decision_id"], malformed)
        self.assertEqual(result["decisions"][0]["selected"]["model"], "model-00")
        self.assertIn("invalid_advisor_result", result["decisions"][0]["reason_codes"])
        prepared, _ = await self.prepare(service)
        abstained = copy.deepcopy(prepared["handoff"]["result_contract"])
        abstained["rankings"][0].update(abstained=True, ranking=[])
        abstained["metadata"]["assessments"][0]["basis"] = "Fixture abstention; no task adequacy conclusion."
        result = service.complete_routing(prepared["decision_id"], abstained)
        self.assertEqual(result["decisions"][0]["selected"]["model"], "model-00")
        self.assertIn("advisor_abstained", result["decisions"][0]["reason_codes"])


class CostObjectiveLifecycleGuards(unittest.IsolatedAsyncioTestCase):
    setUp = AdvisorFallbackLifecycleGuards.setUp
    prepare = AdvisorFallbackLifecycleGuards.prepare

    async def test_objective_survives_disabled_unavailable_and_budget_omitted_evidence(self):
        for unit in ("quota_units", "api_usd"):
            for availability in ("disabled", "unavailable", "omitted"):
                with self.subTest(unit=unit, availability=availability):
                    objective = {"unit": unit, "unit_basis": "private-owner-tariff", "overhead": .05}
                    self.fixture.config = {"schema_version": 4, "telemetry": {"mode": "metadata"},
                                           "task_evidence": {"enabled": availability != "disabled"}}
                    if availability == "omitted":
                        packets = decisions.packets()
                        packets[0]["cost_objective"] = objective
                        size = len(encoded(semantic_projection(decisions.snapshot(task_packets=packets))))
                        self.fixture.config["policy"] = {"schema_version": 3, "max_snapshot_bytes": size + 384}
                    service = self.fixture.service()
                    evidence = service.advisor_workflow.task_evidence
                    summary = {"schema_version": 1, "status": "unavailable", "reason": "fixture_unavailable", "packets": []}
                    if availability == "omitted":
                        summary = {"schema_version": 1, "status": "available", "packets": [
                            {"packet_id": "work-0", "limitations": ["fixture-" + "x" * 400] * 4}]}
                    evidence.async_summarize = AsyncMock(return_value=summary)
                    prepared, snapshot = await self.prepare(service, cost_objectives={"work-0": objective})
                    self.assertEqual(snapshot["packets"][0]["cost_objective"], objective)
                    validate_routing_snapshot(snapshot)
                    if availability == "disabled":
                        evidence.async_summarize.assert_not_awaited()
                    else:
                        evidence.async_summarize.assert_awaited_once()
                        self.assertEqual(prepared["task_evidence_status"],
                                         "omitted_snapshot_budget" if availability == "omitted" else "unavailable")
                    if availability != "unavailable":
                        self.assertNotIn("task_similarity_evidence", snapshot["evidence"])
                    completed = self.fixture.service().complete_routing(prepared["decision_id"], decisions.answer(snapshot),
                                                                        envelope=prepared["envelope"])
                    decision = completed["decisions"][0]
                    self.assertEqual(decision["selected"]["model"], "model-00")
                    self.assertEqual(decision["economic_assessment"]["objective_unit"], unit)
                    self.assertEqual(decision["economic_assessment"]["selection_unit"], "api_usd")
                    self.assertEqual("quota_cost_unknown" in decision["economic_assessment"]["unknowns"], unit == "quota_units")

    async def test_invalid_or_conflicting_objectives_fail_before_acquisition_or_pending_state(self):
        service = self.fixture.service()
        objective = {"unit": "quota_units", "unit_basis": "owner-tariff", "overhead": None}
        packets = decisions.packets()
        packets[0]["cost_objective"] = objective
        invalid_maps = [[], {"foreign": objective}, {"work-0": {**objective, "unit": []}},
                        {"work-0": {**objective, "overhead": True}},
                        *[{"work-0": {**objective, key: value}} for key, value in
                          (("unit", "api_usd"), ("unit_basis", "other-tariff"), ("overhead", .05))]]
        for value in invalid_maps:
            with self.subTest(value=value):
                with self.assertRaises(EvidenceError):
                    await self.prepare(service, packets=copy.deepcopy(packets), cost_objectives=value)
                service.context.assert_not_awaited()
                self.assertEqual(service.advisor_workflow._states, {})
                self.assertIsNone(service.inventory)
        _, snapshot = await self.prepare(service, packets=packets, cost_objectives={"work-0": objective})
        self.assertEqual(snapshot["packets"][0]["cost_objective"], objective)
        summary = {"schema_version": 1, "status": "unavailable", "packets": [
            {"packet_id": "work-0", "cost_objective": objective}]}
        validate_summary(summary)
        summary["packets"][0]["cost_objective"] = {**objective, "unit": []}
        with self.assertRaises(EvidenceError):
            validate_summary(summary)
        for unit in ([], {}, "tokens"):
            with self.subTest(comparison_unit=unit), self.assertRaises(EvidenceError):
                validate_summary({"schema_version": 1, "status": "available", "packets": [
                    {"packet_id": "work-0", "comparison": {"unit": unit, "pairwise_comparisons": []}}]})
        validate_summary({"schema_version": 1, "status": "unavailable", "packets": [
            {"packet_id": "work-0", "comparison": {"unit": None, "pairwise_comparisons": []}}]})

    async def test_objective_is_bound_to_cache_and_portable_replay_but_not_private_metadata(self):
        service = self.fixture.service()
        objective = {"unit": "quota_units", "unit_basis": "private-owner-tariff", "overhead": .125}
        prepared, snapshot = await self.prepare(service, cost_objectives={"work-0": objective})
        answer = decisions.answer(snapshot)
        service.complete_routing(prepared["decision_id"], answer)
        renamed = decisions.packets()
        renamed[0].update(packet_id="renamed", baseline={"model": "model-00", "effort": "low"}, cost_objective=objective)
        cached = await service.prepare_routing(renamed, advisor_route=decisions.ROUTE, portable=True)
        self.assertTrue(cached["cache_hit"])
        self.assertEqual(cached["decisions"][0]["packet_id"], "renamed")
        self.assertEqual(cached["decisions"][0]["economic_assessment"]["objective_unit"], "quota_units")
        changed = copy.deepcopy(renamed)
        changed[0]["cost_objective"]["unit"] = "api_usd"
        fresh = await service.prepare_routing(changed, advisor_route=decisions.ROUTE, portable=True)
        self.assertEqual(fresh["status"], "awaiting_native_advice")
        self.assertFalse(fresh.get("cache_hit", False))
        self.assertNotIn("private-owner-tariff", json.dumps(_external_state(snapshot)))
        metadata = " ".join(path.read_text() for path in (self.fixture.root / "cache").rglob("decision-*.json"))
        self.assertNotIn("private-owner-tariff", metadata)
        self.assertNotIn('"cost_objective"', metadata)
        store = HistoryStore(self.fixture.root / "retained", mode="full", retain_descriptions=True, clock=lambda: self.fixture.now)
        record = store.write_decision("objective-replay", snapshot, answer, decide(snapshot, answer))
        replayed = replay(record)
        self.assertEqual(replayed["decisions"][0]["economic_assessment"]["objective_unit"], "quota_units")
        self.assertEqual(replayed["decisions"][0]["economic_assessment"]["selection_unit"], "api_usd")

    def test_every_objective_field_changes_semantic_identity_and_packet_normalization(self):
        objective = {"unit": "quota_units", "unit_basis": "owner-tariff", "overhead": None}
        packets = decisions.packets()
        packets[0]["cost_objective"] = objective
        normalized = validate_packets(packets)
        self.assertEqual(normalized[0]["cost_objective"], objective)
        first = decisions.snapshot(task_packets=packets)
        for key, value in (("unit", "api_usd"), ("unit_basis", "other-tariff"), ("overhead", .05)):
            with self.subTest(key=key):
                changed = copy.deepcopy(packets)
                changed[0]["cost_objective"][key] = value
                second = decisions.snapshot(task_packets=changed)
                self.assertNotEqual(first["snapshot_id"], second["snapshot_id"])
                self.assertNotEqual(semantic_projection(first), semantic_projection(second))


if __name__ == "__main__":
    unittest.main()
