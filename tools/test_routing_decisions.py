import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

SCRIPTS = Path(__file__).parents[1] / "skills" / "route-subagents" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from route_evidence.advice import build_snapshot, decide, semantic_key
from route_evidence.advice_contracts import DECISION_POLICY, validate_packets
from route_evidence.advisors.native import advisor_input, parse_native, prepare_native
from route_evidence.advisors.jev import _external_state
from route_evidence.advisor_config import migrate_config
from route_evidence.cache import Cache
from route_evidence.core import EvidenceError, encoded
from route_evidence.decision_contracts import question_bindings, result_contract
from route_evidence.history import HistoryStore, replay
from route_evidence.service import RoutingService, load_config

SPEC = {"goal": "Implement a bounded decimal parser with explicit invalid-input errors.",
        "criteria": [{"id": "syntax", "description": "Accept decimal integers only and reject trailing input."},
                     {"id": "range", "description": "Reject values outside the stated bounds without overflow."}],
        "verification": "Run deterministic normal, boundary and invalid-input cases.",
        "error_impact": "low", "ambiguity": "low", "provenance": "caller"}
ROUTE = {"model": "model-00", "effort": "low",
         "selection_basis": {"source": "caller", "reason_code": "bounded_ranking"}}


def context(costs=(.2, .5), scores=(.88, .88), candidate_count=2):
    candidates = [{"model": f"model-{i:02d}", "effort": "low", "score": scores[i],
                   "expenses": {"cost_usd": costs[i]} if costs[i] is not None else {},
                   "cost_basis": "fixture_usd_per_task"} for i in range(len(costs))]
    comparison = {"source_id": "synthetic", "version": "fixture", "subset": "all", "harness": "fixture",
                  "metric": "pass_at_1", "protocol": "fixture-only", "expense_axes": ["cost_usd"],
                  "candidates": candidates}
    return {"schema_version": 2, "client": "test-client", "task_types": ["implementation"],
            "inventory": [{"model": f"model-{i:02d}", "effort": "low"} for i in range(candidate_count)],
            "tasks": [{"task_type": "implementation", "primary_comparisons": [comparison], "supporting_comparisons": []}],
            "sources": [], "guidance": {}, "declared_constraints": {}}


def packets(count=1):
    return [{"packet_id": f"work-{i}", "task_types": ["implementation"], "features": {},
             "task_spec": copy.deepcopy(SPEC)} for i in range(count)]


def snapshot(*, costs=(.2, .5), scores=(.88, .88), count=2, packet_count=1, task_packets=None, ctx=None):
    return build_snapshot(ctx or context(costs, scores, count), task_packets or packets(packet_count),
                          policy=DECISION_POLICY, client="test-client", created_at="2030-01-01T00:00:00Z",
                          expires_at="2030-01-01T00:10:00Z")


def answer(snap, choices=None):
    value = result_contract(snap, ROUTE["model"], ROUTE["effort"], "native-decisions-v1")
    choices = choices or {}
    for assessment in value["assessments"]:
        cohort_ids = [c["cohort_id"] for c in snap["evidence"]["cohorts"]]
        assessment["bases"] = [{"id": "a", "kind": "task_inference", "criterion_ids": ["syntax", "range"],
                                "cohort_ids": cohort_ids, "explanation": "The bounded scope and deterministic oracle support this task inference.",
                                "unknowns": ["quality_transfer"]}]
    bindings = question_bindings(snap)
    for item in value["answers"]:
        packet_id, candidate_id = bindings[item["name"]]
        candidate = next(c for c in snap["candidates"] if c["candidate_id"] == candidate_id)
        choice = choices.get(candidate["model"], "adequate")
        item.update(choice=choice, basis="a")
        if choice == "unknown":
            assessment = next(a for a in value["assessments"] if a["packet_id"] == packet_id)
            if not any(b["id"] == "u" for b in assessment["bases"]):
                assessment["bases"].append({"id": "u", "kind": "unknown", "criterion_ids": [], "cohort_ids": [],
                                          "explanation": "Material task adequacy evidence is unavailable.", "unknowns": ["task_adequacy"]})
            item["basis"] = "u"
    return value


class DecisionContractTests(unittest.TestCase):
    def test_actual_producer_contract_round_trip_with_independent_cost_expectation(self):
        snap = snapshot()
        available = [{"model": c["model"], "efforts": [c["effort"]]} for c in snap["candidates"]]
        prepared = prepare_native(snap, ROUTE, available=available)
        request = json.loads(prepared["prompt"].split("\nDecision request:\n")[1])
        self.assertEqual(request["input"]["snapshot"], snap)
        self.assertEqual(len(request["questions"]), 2)
        self.assertEqual({q["type"] for q in request["questions"]}, {"choice"})
        self.assertNotIn("rankings", prepared["result_contract"])
        actual = parse_native(snap, answer(snap), advisor_route=ROUTE)
        selected = decide(snap, actual)[0]
        self.assertEqual(selected["selected"]["model"], "model-00")
        self.assertEqual(selected["ranking"], [])
        self.assertIn("benchmark_cost_selected", selected["reason_codes"])
        self.assertEqual(prepared["descriptor"]["privacy_profile"], "native-task-spec-v1")
        private = advisor_input(snap, ROUTE)
        self.assertEqual(private["result_contract"]["metadata"]["contract_version"], "native-decisions-private-v2")

    def test_omitted_optional_unknowns_do_not_erase_or_supply_adequacy(self):
        snap = snapshot()
        value = answer(snap)
        value["assessments"][0]["bases"][0].pop("unknowns")
        original = copy.deepcopy(value)
        parsed = parse_native(snap, value)
        self.assertEqual(value, original)
        self.assertEqual(parsed["answers"], original["answers"])
        self.assertEqual(parsed["assessments"][0]["bases"][0]["unknowns"], [])
        self.assertEqual(decide(snap, parsed)[0]["selected"]["model"], "model-00")
        value = answer(snap, {"model-00": "unknown"})
        value["assessments"][0]["bases"][1].pop("unknowns")
        with self.assertRaisesRegex(EvidenceError, "unknown_basis_required"):
            parse_native(snap, value)

    def test_legacy_cost_refs_are_not_a_new_economic_decision(self):
        from test_routing_adapters import native_result
        snap = snapshot()
        old = native_result(snap)
        old["metadata"]["assessments"] = [{"packet_id": "work-0", "cohort_ids": [snap["evidence"]["cohorts"][0]["cohort_id"]],
                                            "basis": "Highest quality preferred; task adequacy is uncertain."}]
        with self.assertRaisesRegex(EvidenceError, "native_decision_answers_required"):
            parse_native(snap, old)

    def test_named_answer_and_basis_validation(self):
        snap = snapshot()
        for mutate, error in [
            (lambda r: r["answers"].pop(), "answers_required"),
            (lambda r: r["answers"].append(copy.deepcopy(r["answers"][0])), "answers_required"),
            (lambda r: r["answers"][1].update(name=r["answers"][0]["name"]), "question_invalid"),
            (lambda r: r["answers"][0].update(choice="best"), "choice_invalid"),
            (lambda r: r["answers"][0].update(basis="missing"), "answer_basis_invalid"),
            (lambda r: r["assessments"][0]["bases"][0].update(criterion_ids=["invented"]), "criterion_ids_invalid"),
            (lambda r: r["assessments"][0]["bases"][0].update(criterion_ids=["syntax"]), "all_task_criteria_required"),
            (lambda r: r["assessments"][0]["bases"][0].update(cohort_ids=["foreign"]), "cohort_ids_invalid"),
            (lambda r: r.update(confidence=.99), "numeric_confidence_forbidden"),
            (lambda r: r["assessments"][0]["bases"][0].update(kind="unknown"), "task_criterion_required"),
            (lambda r: r["assessments"][0]["bases"][0].update(kind=[]), "basis_kind_invalid"),
        ]:
            with self.subTest(error=error):
                bad = answer(snap)
                mutate(bad)
                with self.assertRaisesRegex(EvidenceError, error):
                    parse_native(snap, bad)

    def test_sparse_measurement_cannot_be_claimed_for_an_unmeasured_pair(self):
        snap = snapshot(count=3)
        value = answer(snap)
        value["assessments"][0]["bases"][0]["kind"] = "measurement"
        with self.assertRaisesRegex(EvidenceError, "exact_measurement_required"):
            parse_native(snap, value)
        self.assertEqual(len(parse_native(snap, answer(snap))["answers"]), 3)

    def test_max_batch_keeps_all_candidates_and_fits_existing_result_bound(self):
        snap = snapshot(count=64, packet_count=8)
        value = parse_native(snap, answer(snap))
        self.assertEqual(len(value["answers"]), 512)
        self.assertLess(len(encoded(value)), 65536)
        self.assertEqual([len(p["eligible"]) for p in snap["packets"]], [64] * 8)

    def test_task_spec_is_native_only_and_changes_semantic_identity(self):
        snap = snapshot()
        external = json.dumps(_external_state(snap))
        self.assertNotIn(SPEC["goal"], external)
        self.assertNotIn("task_spec", external)
        changed = packets()
        changed[0]["task_spec"]["verification"] = "A reviewed proof is required in addition to tests."
        second = snapshot(task_packets=changed)
        descriptor = prepare_native(snap, ROUTE, available=[{"model": "model-00", "efforts": ["low"]}])["descriptor"]
        self.assertNotEqual(semantic_key(snap, descriptor), semantic_key(second, descriptor))
        for text in ("C:/private/source.py", "password=private", "```code```"):
            bad = packets()
            bad[0]["task_spec"]["goal"] = text
            with self.assertRaises(EvidenceError):
                validate_packets(bad)

    def test_missing_task_details_is_a_bootstrap_outcome(self):
        raw = packets()
        raw[0].pop("task_spec")
        snap = snapshot(task_packets=raw)
        handoff = prepare_native(snap, ROUTE, available=[{"model": "model-00", "efforts": ["low"]}])
        self.assertEqual(handoff["status"], "needs_task_details")
        self.assertNotIn("prompt", handoff)


class EconomicPolicyTests(unittest.TestCase):
    def decision(self, costs=(.2, .5), *, scores=(.88, .88), choices=None, ctx=None, raw=None):
        snap = snapshot(costs=costs, scores=scores, ctx=ctx, task_packets=raw)
        return decide(snap, parse_native(snap, answer(snap, choices)))[0]

    def test_only_cost_changes_the_selection_without_a_local_history(self):
        self.assertEqual(self.decision()["selected"]["model"], "model-00")
        self.assertEqual(self.decision((.5, .2))["selected"]["model"], "model-01")

    def test_premium_score_does_not_override_task_sufficiency(self):
        self.assertEqual(self.decision(scores=(.60, .99))["selected"]["model"], "model-00")

    def test_cheap_inadequate_route_cannot_win(self):
        decision = self.decision(choices={"model-00": "inadequate"})
        self.assertEqual(decision["selected"]["model"], "model-01")

    def test_unknown_and_absent_cost_are_qualified_not_zero(self):
        decision = self.decision((None, None))
        self.assertIn("comparable_cost_unknown", decision["reason_codes"])
        self.assertNotIn("benchmark_cost_selected", decision["reason_codes"])
        decision = self.decision(choices={"model-00": "unknown", "model-01": "unknown"})
        self.assertIsNone(decision["selected"])
        self.assertIn("task_adequacy_unknown", decision["reason_codes"])

    def test_baseline_and_answer_order_do_not_change_selection(self):
        for baseline in ("model-00", "model-01"):
            raw = packets()
            raw[0]["baseline"] = {"model": baseline, "effort": "low"}
            snap = snapshot(task_packets=raw)
            value = answer(snap)
            value["answers"].reverse()
            self.assertEqual(decide(snap, parse_native(snap, value))[0]["selected"]["model"], "model-00")

    def test_conflicting_comparable_cohorts_do_not_produce_a_fake_winner(self):
        ctx = context()
        other = copy.deepcopy(context((.8, .1))["tasks"][0]["primary_comparisons"][0])
        other["harness"] = "other-fixture"
        ctx["tasks"][0]["primary_comparisons"].append(other)
        decision = self.decision(ctx=ctx)
        self.assertIsNone(decision["selected"])
        self.assertIn("cost_cohort_conflict", decision["reason_codes"])

    def test_incomparable_cost_bases_do_not_claim_measured_savings(self):
        ctx = context()
        ctx["tasks"][0]["primary_comparisons"][0]["candidates"][1]["cost_basis"] = "different-measurement-mode"
        decision = self.decision(ctx=ctx)
        self.assertIn("comparable_cost_unknown", decision["reason_codes"])

    def test_disjoint_cost_groups_are_uncertain_not_contradictory(self):
        ctx = context(candidate_count=4)
        other = copy.deepcopy(ctx["tasks"][0]["primary_comparisons"][0])
        other["harness"] = "disjoint-fixture"
        for row, model in zip(other["candidates"], ("model-02", "model-03")):
            row["model"] = model
        ctx["tasks"][0]["primary_comparisons"].append(other)
        snap = snapshot(count=4, ctx=ctx)
        decision = decide(snap, parse_native(snap, answer(snap)))[0]
        self.assertIn(decision["selected"]["model"], {"model-00", "model-02"})
        self.assertNotIn("cost_cohort_conflict", decision["reason_codes"])
        self.assertIn("cost_groups_incomparable", decision["economic_assessment"]["unknowns"])
        self.assertNotIn("economic_tie", decision["reason_codes"])
        bridge = copy.deepcopy(other)
        bridge["harness"] = "bridge-fixture"
        bridge["candidates"][0].update(model="model-02", expenses={"cost_usd": .1})
        bridge["candidates"][1].update(model="model-00", expenses={"cost_usd": .25})
        ctx["tasks"][0]["primary_comparisons"].append(bridge)
        snap = snapshot(count=4, ctx=ctx)
        decision = decide(snap, parse_native(snap, answer(snap)))[0]
        self.assertEqual(decision["selected"]["model"], "model-02")
        self.assertNotIn("cost_groups_incomparable", decision["economic_assessment"]["unknowns"])

    def test_supported_paired_chain_cost_can_change_the_benchmark_choice(self):
        from route_evidence.task_evidence import attach_summary
        from route_evidence.task_costs import compare
        snap = snapshot()
        ids = {c["model"]: c["candidate_id"] for c in snap["candidates"]}
        rows = [{"task_id": str(i), "model": model, "effort": "low", "complete": True,
                 "score": 1, "metric": "accepted", "comparison_basis": "paired-fixture", "cost_scope": "chain",
                 "costs": {"api_usd": cost}, "unit_basis": {"api_usd": "fixture-tariff"}}
                for i in range(3) for model, cost in (("model-00", 2.), ("model-01", .4))]
        paired = compare(rows, snap["candidates"], ids["model-00"], "api_usd", .05)
        summary = {"schema_version": 1, "status": "available", "mode": "structured",
                   "cost_units_are_not_interchangeable": True, "packets": [{"packet_id": "work-0", "comparison": paired}]}
        snap = attach_summary(snap, summary)
        decision = decide(snap, parse_native(snap, answer(snap)))[0]
        self.assertEqual(decision["selected"]["model"], "model-01")
        self.assertIn("paired_chain_cost_selected", decision["reason_codes"])
        self.assertIn("observational_cost_transfer", decision["economic_assessment"]["unknowns"])


class DecisionLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.now = 1800000000.0
        self.config = {"schema_version": 4, "telemetry": {"mode": "metadata"}}

    def service(self):
        service = RoutingService(Cache(self.root / "cache", clock=lambda: self.now), client="test-client",
                                 clock=lambda: self.now, advisor_config=self.config)
        service.context = AsyncMock(return_value=context())
        return service

    async def test_portable_completion_cache_rebinding_and_history_privacy(self):
        service = self.service()
        kwargs = {"available": [{"model": "model-00", "efforts": ["low"]}, {"model": "model-01", "efforts": ["low"]}],
                  "advisor_route": ROUTE, "portable": True}
        prepared = await service.prepare_routing(packets(), **kwargs)
        self.assertEqual(prepared["status"], "awaiting_native_advice")
        snap = prepared["envelope"]["payload"]["snapshot"]
        result = answer(snap)
        completed = self.service().complete_routing(prepared["decision_id"], result, envelope=prepared["envelope"])
        self.assertEqual(completed["decisions"][0]["selected"]["model"], "model-00")
        service.complete_routing(prepared["decision_id"], result)
        renamed = packets()
        renamed[0]["packet_id"] = "renamed-work"
        cached = await service.prepare_routing(renamed, **kwargs)
        self.assertTrue(cached["cache_hit"])
        self.assertEqual(cached["advisor_result"]["assessments"][0]["packet_id"], "renamed-work")
        self.assertEqual(cached["decisions"][0]["selected"]["model"], "model-00")
        raw_history = " ".join(p.read_text(encoding="utf-8") for p in (self.root / "cache").rglob("decision-*.json"))
        self.assertNotIn(SPEC["goal"], raw_history)
        self.assertNotIn("The bounded scope", raw_history)
        self.assertIn("benchmark_cost_selected", raw_history)

    async def test_full_history_requires_description_retention_for_replay(self):
        snap = snapshot()
        value = answer(snap)
        store = HistoryStore(self.root / "private", mode="full", clock=lambda: self.now)
        record = store.write_decision("new-contract", snap, value, decide(snap, value))
        self.assertNotIn("full", record)
        self.assertEqual(record["full_unavailable_reason"], "native_task_description_not_retained")
        self.assertEqual(replay(record)["status"], "insufficient_record")
        store.retain_descriptions = True
        record = store.write_decision("new-contract-retained", snap, value, decide(snap, value))
        self.assertEqual(replay(record)["decisions"][0]["selected"]["model"], "model-00")

    async def test_explicit_config_migration_preserves_source_and_pipeline(self):
        source = self.root / "old.json"
        original = encoded({"schema_version": 3, "client": "test-client", "pipeline": {"mode": "evidence-only"}})
        source.write_bytes(original)
        target = self.root / "new.json"
        migrate_config(source, target, native_decisions=True)
        self.assertEqual(source.read_bytes(), original)
        actual = load_config(target)
        self.assertEqual(actual["schema_version"], 4)
        self.assertEqual(actual["policy"]["policy_version"], "routing-policy-v3")
        self.assertEqual(actual["pipeline"]["mode"], "evidence-only")
        self.assertIsNone(actual["policy"]["max_snapshot_bytes"])

    async def test_required_claude_consumes_named_answers_without_root_evidence(self):
        from test_routing_pipeline import PipelineTests
        fixture = PipelineTests("runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.config["schema_version"] = 4
        fixture.config["policy"] = {"schema_version": 3}
        fixture.configure()
        prepared = await fixture.prepare(packets=[{"packet_id": "work", "task_types": ["implementation"],
                                                   "features": {}, "task_spec": SPEC}])
        fixture.launch(prepared["handoff"])
        private = fixture.private_input(prepared["decision_id"])
        snap = json.loads(private["prompt"].split("\nDecision request:\n")[1])["input"]["snapshot"]
        value = answer(snap)
        for key in ("requested_model", "resolved_model", "effort", "metadata"):
            value[key] = private["result_contract"][key]
        fixture.submit(prepared["decision_id"], value)
        fixture.event("PostToolUse", tool_name="Agent", tool_use_id="call-a",
                      tool_response={"status": "completed", "agentId": "advisor-a", "content": []})
        decision = fixture.decision(prepared["decision_id"])
        self.assertEqual(decision["decisions"][0]["decision_type"], "advisor")
        self.assertNotIn(SPEC["goal"], json.dumps(decision))
        self.assertNotIn('"answers"', json.dumps(decision))
        worker = fixture.authorize(prepared["decision_id"])
        self.assertEqual(worker["requested_model"], decision["decisions"][0]["selected"]["model"])
        self.assertIn("PRIVATE_WORK_PROMPT", fixture.dispatched(worker, "worker-call")["prompt"])


if __name__ == "__main__":
    unittest.main()
