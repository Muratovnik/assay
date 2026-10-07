"""Synthetic host/protocol tests. No native agent or model-quality claims."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "route-subagents" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from route_evidence.cache import Cache
from route_evidence.claude_agents import alias_efforts, generate, resolve_variant
from route_evidence.core import EvidenceError, timestamp
from route_evidence.pipeline import RoutingPipeline
from route_evidence.pipeline_config import configured_inventory, confirm_inventory, inventory_ttl_seconds, settings
from route_evidence.pipeline_store import PipelineStore
from route_evidence.routing import build_context
from route_evidence.service import RoutingService, load_config
from routing_hook import handle
from claude_output_fixture import assert_agent_output, completed_output

AVAILABLE = [{"model": "worker-alpha", "efforts": ["low", "high"]},
             {"model": "worker-beta", "efforts": ["medium"]}]
ROUTE = {"model": "worker-beta", "effort": "medium",
         "selection_basis": {"source": "client_role", "reason_code": "bounded_ranking"}}
BASELINE = {"model": "worker-alpha", "effort": "low"}
PACKETS = [{"packet_id": "work", "task_types": ["implementation"], "features": {}}]


class PipelineTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.now = time.time()
        self.path = self.root / "config.json"
        self.config = {"schema_version": 3, "client": "claude", "telemetry": {"mode": "off"},
            "inventory": {"available": AVAILABLE, "observed_at": timestamp(self.now)},
            "pipeline": {"mode": "required", "state_dir": str(self.root / "state"), "agents_dir": str(self.root / "agents"),
                "advisor_route": ROUTE, "baseline": BASELINE,
                "variants": [{"profile": "general-purpose", "model": m["model"], "effort": e}
                             for m in AVAILABLE for e in m["efforts"]]}}
        self.configure()

    def configure(self):
        self.path.write_text(json.dumps(self.config), encoding="utf-8")
        self.config = load_config(self.path)
        # As claude-routes does: an effort definition per alias effort in the inventory.
        generate(settings(self.config), {}, efforts=alias_efforts((configured_inventory(self.config) or {}).get("available", [])))
        self.service = self.make_service()
        self.pipeline = RoutingPipeline(self.service)
        self.event("SessionStart")

    def make_service(self):
        service = RoutingService(Cache(self.root / "cache", clock=lambda: self.now),
            client="claude", clock=lambda: self.now, advisor_config=self.config,
            inventory=configured_inventory(self.config), inventory_ttl=inventory_ttl_seconds(self.config))
        async def context(request):
            return {**build_context(request, []), "sources": [], "data_status": "unavailable",
                    "data_message": "synthetic-only", "usage": "routing"}
        service.context = AsyncMock(side_effect=context)
        return service

    def event(self, name, *, agent=None, session="session-a", scope="plugin", **fields):
        event = {"hook_event_name": name, "session_id": session, **fields}
        if agent is not None:
            event["agent_id"] = agent
        return handle(event, self.config, scope=scope, clock=lambda: self.now,
                      environment={"CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"})

    def rpc(self, tool, arguments, *, agent=None, session="session-a", **fields):
        result = self.event("PreToolUse", agent=agent, session=session,
            tool_name="mcp__assay-benchmark-routing__" + tool,
            tool_input=arguments, **fields)
        specific = result.get("hookSpecificOutput", {})
        if specific.get("permissionDecision") == "deny":
            raise EvidenceError(specific["permissionDecisionReason"])
        self.assertIn("updatedInput", specific)
        return specific["updatedInput"]

    async def prepare(self, **changes):
        args = {"packets": copy.deepcopy(PACKETS),
                "launch_requests": {"work": {"profile": "general-purpose", "prompt": "PRIVATE_WORK_PROMPT: implement only the bounded packet."}}, **changes}
        return await self.pipeline.prepare(self.rpc("prepare_routing", args))

    def dispatched(self, launch, tool_id):
        reply = self.event("PreToolUse", tool_name="Agent", tool_use_id=tool_id, tool_input=launch["input"])
        specific = reply["hookSpecificOutput"]
        # The host substitutes the registered input; the stub carries no prompt
        # and the hook grants no permission of its own.
        self.assertNotIn("permissionDecision", specific)
        self.assertEqual(specific["updatedInput"]["subagent_type"], launch["input"]["subagent_type"])
        return specific["updatedInput"]

    def launch(self, launch, *, agent="advisor-a", tool_id="call-a", **fields):
        full = self.dispatched(launch, tool_id)
        self.event("SubagentStart", agent=agent, agent_type=launch["input"]["subagent_type"], **fields)
        return full

    def private_input(self, decision_id, agent="advisor-a"):
        level = settings(self.config)["advisor_route"]["effort"]
        return self.pipeline.advisor_input(self.rpc("get_advisor_input", {"decision_id": decision_id}, agent=agent, effort={"level": level}))

    def submit(self, decision_id, answer, agent="advisor-a"):
        return self.pipeline.complete(self.rpc("complete_routing", {"decision_id": decision_id, "advisor_result": answer}, agent=agent))

    async def decided(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        private = self.private_input(prepared["decision_id"])
        self.submit(prepared["decision_id"], private["result_contract"])
        self.event("PostToolUse", tool_name="Agent", tool_use_id="call-a", tool_response={"status": "completed", "agentId": "advisor-a", "content": []})
        self.decision(prepared["decision_id"])
        return prepared["decision_id"]

    def decision(self, decision_id):
        return self.pipeline.decision(self.rpc("get_routing_decision", {"decision_id": decision_id}))

    def authorize(self, decision_id, **extra):
        return self.pipeline.authorize(self.rpc("authorize_routing_launch", {"decision_id": decision_id, "packet_id": "work", **extra}))

    async def test_complete_chain_keeps_evidence_and_raw_task_out_of_root_and_advisor_respectively(self):
        prepared = await self.prepare()
        encoded = json.dumps(prepared)
        for forbidden in ("Routing snapshot data:", "result_contract", '"ranking"', '"candidates"', "PRIVATE_WORK_PROMPT"):
            self.assertNotIn(forbidden, encoded)
        self.launch(prepared["handoff"])
        private = self.private_input(prepared["decision_id"])
        self.assertIn("Routing snapshot data:", private["prompt"])
        self.assertNotIn("PRIVATE_WORK_PROMPT", json.dumps(private))
        self.submit(prepared["decision_id"], private["result_contract"])
        self.event("PostToolUse", tool_name="Agent", tool_use_id="call-a", tool_response={"status": "completed", "content": []})
        result = self.decision(prepared["decision_id"])
        self.assertEqual(result["status"], "decided")
        self.assertNotIn('"ranking"', json.dumps(result))
        self.assertEqual(result["advisor_provenance"]["observed_effort"], "medium")
        self.assertIsNone(result["advisor_provenance"]["observed_model"])
        worker = self.authorize(prepared["decision_id"])
        self.assertNotIn("PRIVATE_WORK_PROMPT", json.dumps(worker))
        self.assertIn("PRIVATE_WORK_PROMPT", self.launch(worker, agent="worker-a", tool_id="call-worker")["prompt"])

    async def test_root_cannot_fetch_private_input_or_submit_a_valid_answer(self):
        prepared = await self.prepare()
        for tool, args in (("get_advisor_input", {"decision_id": prepared["decision_id"]}),
                           ("complete_routing", {"decision_id": prepared["decision_id"], "advisor_result": {}})):
            with self.subTest(tool=tool), self.assertRaises(EvidenceError):
                self.rpc(tool, args)
        with self.assertRaisesRegex(EvidenceError, "receipt"):
            self.pipeline.complete({"decision_id": prepared["decision_id"], "advisor_result": {}})

    async def test_receipt_is_one_use_argument_bound_and_session_bound(self):
        receipt = self.rpc("prepare_routing", {"packets": PACKETS, "launch_requests": {}})
        changed = {**receipt, "available": AVAILABLE[:1]}
        with self.assertRaises(EvidenceError):
            self.pipeline.host("prepare_routing", changed)
        self.pipeline.host("prepare_routing", receipt)
        with self.assertRaises(EvidenceError):
            self.pipeline.host("prepare_routing", receipt)
        prepared = await self.prepare()
        self.event("SessionStart", session="session-b")
        with self.assertRaises(EvidenceError):
            self.pipeline.decision(self.rpc("get_routing_decision", {"decision_id": prepared["decision_id"]}, session="session-b"))

    async def test_inventory_and_runtime_capability_mask_cannot_fake_single_candidate(self):
        for change in ({"available": [AVAILABLE[0]]},
                       {"packets": [{**PACKETS[0], "capabilities": [{"model": "worker-alpha", "effort": "low", "route_expressible": False, "capabilities": {}}]}]}):
            with self.subTest(change=change), self.assertRaises(EvidenceError):
                await self.prepare(**change)
        self.service.context.assert_not_called()

    async def test_stale_configured_inventory_cannot_be_refreshed_by_repeating_it(self):
        self.now += 86401
        self.event("SessionStart")
        with self.assertRaisesRegex(EvidenceError, "inventory_expired"):
            await self.prepare(available=AVAILABLE)
        self.service.context.assert_not_called()

    async def test_uncertified_fallback_is_rejected(self):
        with self.assertRaisesRegex(EvidenceError, "authority"):
            await self.prepare(packets=[{**PACKETS[0], "baseline": {"model": "worker-alpha", "effort": "high"}}])

    async def test_user_choice_is_honored_only_for_a_generated_inventory_pair(self):
        chosen = {"model": "worker-alpha", "effort": "high"}
        with patch("route_evidence.advisors.native.prepare_native", side_effect=AssertionError("must skip")):
            prepared = await self.prepare(packets=[{**PACKETS[0], "explicit": chosen, "explicit_source": "user"}])
        self.assertNotIn("handoff", prepared)
        decision = prepared["decisions"][0]
        self.assertEqual(decision["decision_type"], "explicit_user_choice")
        self.assertEqual({k: decision["selected"][k] for k in chosen}, chosen)
        self.assertEqual(self.authorize(prepared["decision_id"])["requested_effort"], "high")
        # Outside the confirmed inventory the choice is refused, not replaced.
        refused = await self.prepare(packets=[{**PACKETS[0], "explicit": {"model": "worker-alpha", "effort": "max"}}])
        self.assertEqual(refused["decisions"][0]["reason_codes"], ["invalid_explicit_choice"])
        self.assertIsNone(refused["decisions"][0]["selected"])
        # An inventory pair without a generated definition cannot be expressed.
        self.config["pipeline"]["variants"] = [v for v in self.config["pipeline"]["variants"] if v["effort"] != "high"]
        self.configure()
        missing = await self.prepare(packets=[{**PACKETS[0], "explicit": chosen}])
        self.assertEqual(missing["decisions"][0]["reason_codes"], ["invalid_explicit_choice"])

    async def test_configured_choice_rejects_a_contradicting_request(self):
        self.config["pipeline"]["approved_choices"] = {"work": {"model": "worker-alpha", "effort": "high"}}
        self.configure()
        with self.assertRaisesRegex(EvidenceError, "conflicts_with_configured_choice"):
            await self.prepare(packets=[{**PACKETS[0], "explicit": {"model": "worker-beta", "effort": "medium"}}])

    async def test_configured_choice_skips_advisor_but_still_gates_dispatch(self):
        pair = {"model": "worker-alpha", "effort": "high"}
        self.config["pipeline"]["approved_choices"] = {"work": pair}
        self.configure()
        with patch("route_evidence.advisors.native.prepare_native", side_effect=AssertionError("must skip")):
            prepared = await self.prepare(packets=[{**PACKETS[0], "explicit": pair}])
        self.assertNotIn("handoff", prepared)
        self.assertEqual(prepared["decisions"][0]["decision_type"], "configured_choice")
        self.assertEqual("deny", self.event("PreToolUse", tool_name="Agent", tool_use_id="a", tool_input={"prompt": "skip"})["hookSpecificOutput"]["permissionDecision"])
        self.launch(self.authorize(prepared["decision_id"]), agent="worker-a")

    async def test_valid_cache_skips_second_advisor_but_creates_new_decision(self):
        first = await self.decided()
        again = await self.prepare()
        self.assertTrue(again["cache_hit"])
        self.assertNotEqual(again["decision_id"], first)
        self.assertNotIn("handoff", again)
        self.launch(self.authorize(again["decision_id"]), agent="worker-a", tool_id="worker-call")

    async def test_advisor_identity_is_bound_to_one_decision(self):
        prepared = await self.prepare()
        other = await self.prepare()
        self.launch(prepared["handoff"])
        with self.assertRaises(EvidenceError):
            self.private_input(other["decision_id"])
        with self.assertRaises(EvidenceError):
            self.private_input(prepared["decision_id"], "unregistered-agent")

    async def test_advisor_cannot_recurse_and_the_host_allowlist_removes_other_tools(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        for tool in ("Agent", "mcp__assay-benchmark-routing__prepare_routing"):
            with self.subTest(tool=tool):
                reply = self.event("PreToolUse", agent="advisor-a", tool_name=tool, tool_input={})
                self.assertEqual(reply["hookSpecificOutput"]["permissionDecision"], "deny")
        # Ordinary tools are not in the advisor's definition at all; the host
        # enforces that list, so the definition carries no hook of its own.
        advisor = resolve_variant(settings(self.config), "routing-advisor", ROUTE, environment={})
        text = (self.root / "agents" / advisor["file"]).read_text(encoding="utf-8")
        self.assertIn("- mcp__assay-benchmark-routing__get_advisor_input\n", text)
        self.assertNotIn("hooks:", text)
        # A definition generated by an earlier release still calls its own hook; it answers nothing.
        self.assertEqual(self.event("PreToolUse", agent="advisor-a", tool_name="Bash", tool_input={}, scope="agent"), {})

    async def test_observed_effort_mismatch_is_not_reported_as_success(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        with self.assertRaisesRegex(EvidenceError, "effort"):
            self.rpc("get_advisor_input", {"decision_id": prepared["decision_id"]}, agent="advisor-a", effort={"level": "high"})

    async def test_launch_arguments_expiry_and_replays_are_checked(self):
        decision = await self.decided()
        worker = self.authorize(decision)
        changed = copy.deepcopy(worker["input"])
        changed["prompt"] += " do other work"
        self.assertEqual("deny", self.event("PreToolUse", tool_name="Agent", tool_use_id="w", tool_input=changed)["hookSpecificOutput"]["permissionDecision"])
        event = dict(tool_name="Agent", tool_use_id="w", tool_input=worker["input"])
        first = self.dispatched(worker, "w")
        self.assertEqual(first, self.dispatched(worker, "w"))  # a redelivered call is not a new launch
        self.assertEqual("deny", self.event("PreToolUse", **{**event, "tool_use_id": "other"})["hookSpecificOutput"]["permissionDecision"])
        self.now += 601
        self.assertEqual("deny", self.event("PreToolUse", **event)["hookSpecificOutput"]["permissionDecision"])

    async def test_file_edit_after_authorization_blocks_native_launch(self):
        decision = await self.decided()
        launch = self.authorize(decision)
        path = self.root / "agents" / (launch["input"]["subagent_type"] + ".md")
        path.write_text(path.read_text() + "\nforeign change\n")
        with self.assertRaises(EvidenceError):
            self.event("PreToolUse", tool_name="Agent", tool_use_id="w", tool_input=launch["input"])

    def assert_fallback(self, result, cause):
        """The configured baseline, recorded with the reason it was needed."""
        self.assertEqual(result["status"], "decided")
        decision = result["decisions"][0]
        self.assertEqual(decision["decision_type"], "fallback")
        self.assertEqual({k: decision["selected"][k] for k in BASELINE}, BASELINE)
        self.assertEqual(decision["reason_codes"], [cause, "caller_baseline"])
        self.assertNotIn('"ranking"', json.dumps(result))

    async def test_failed_advisor_uses_only_configured_baseline(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        self.event("PostToolUseFailure", tool_name="Agent", tool_use_id="call-a")
        self.assert_fallback(self.decision(prepared["decision_id"]), "advisor_ended_without_result")

    async def test_advisor_ending_without_result_falls_back_instead_of_inheriting_parent(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        self.event("SubagentStop", agent="advisor-a")
        self.event("PostToolUse", tool_name="Agent", tool_use_id="call-a", tool_response={"status": "completed", "content": []})
        self.assert_fallback(self.decision(prepared["decision_id"]), "advisor_ended_without_result")
        launch = self.authorize(prepared["decision_id"])
        self.assertEqual((launch["requested_model"], launch["requested_effort"]), (BASELINE["model"], BASELINE["effort"]))

    async def test_abstaining_advisor_falls_back_to_the_baseline(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        answer = self.private_input(prepared["decision_id"])["result_contract"]
        answer["rankings"][0].update(abstained=True, ranking=[], ties=[])
        self.submit(prepared["decision_id"], answer)
        self.event("SubagentStop", agent="advisor-a")
        self.event("PostToolUse", tool_name="Agent", tool_use_id="call-a", tool_response={"status": "completed", "content": []})
        self.assert_fallback(self.decision(prepared["decision_id"]), "advisor_abstained")

    async def test_disabled_advisor_falls_back_without_a_handoff(self):
        self.config["advisor"] = {"enabled": False, "backend": "native-economy"}
        self.configure()
        prepared = await self.prepare()
        self.assertNotIn("handoff", prepared)
        self.assert_fallback(prepared, "advisor_disabled")

    async def test_required_mode_without_baseline_is_not_set_up(self):
        self.config["pipeline"]["baseline"] = None
        self.config["pipeline"]["unrouted_agents"] = {"Explore": "baseline", "Plan": "inherit"}
        self.configure()
        status = self.pipeline.status()
        self.assertEqual((status["status"], status["setup_gaps"]), ("setup_required", ["baseline"]))
        self.assertFalse(status["baseline_configured"])
        # The hook issues no receipt; the server names the gap instead.
        self.assertEqual(self.event("PreToolUse", tool_name="mcp__assay-benchmark-routing__prepare_routing",
                                    tool_input={"packets": PACKETS}), {})
        with self.assertRaisesRegex(EvidenceError, "setup_incomplete:baseline"):
            await self.pipeline.prepare({"packets": copy.deepcopy(PACKETS), "launch_requests": {
                "work": {"profile": "general-purpose", "prompt": "bounded"}}})
        self.service.context.assert_not_called()
        start = self.event("SessionStart")["hookSpecificOutput"]["additionalContext"]
        self.assertIn("not set up", start)
        denied = self.event("PreToolUse", tool_name="Agent", tool_use_id="t",
                            tool_input={"subagent_type": "general-purpose", "prompt": "work"})
        self.assertIn("setup is incomplete", denied["hookSpecificOutput"]["permissionDecisionReason"])
        # An exempt type without a model of its own needs the baseline's, while
        # an explicit inherit does not.
        exempt = self.event("PreToolUse", tool_name="Agent", tool_use_id="t2",
                            tool_input={"subagent_type": "Explore", "prompt": "find"})
        self.assertIn("unrouted_agent_needs_baseline", exempt["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertEqual(self.event("PreToolUse", tool_name="Agent", tool_use_id="t3",
                                    tool_input={"subagent_type": "Plan", "prompt": "plan"}), {})

    async def test_doctor_reports_unnamed_models_with_candidate_spellings(self):
        from route_evidence.providers import SOURCES, snapshot
        from route_evidence.service import ingest
        rows = [{"model": label, "effort": "medium", "harness": "fixture", "subset": "all", "metric": "pass_at_1",
                 "protocol": "synthetic", "score": .8} for label in ("Worker Alpha", "Worker Beta 2")]
        ingest(self.service.cache, snapshot(SOURCES["frontiercode"], rows), timestamp(self.now))
        names = {m["model"]: m for m in self.service.status()["model_names"]["models"]}
        self.assertEqual(names["worker-alpha"]["named_in"], ["frontiercode"])
        self.assertEqual(names["worker-beta"]["unnamed_in"], ["frontiercode"])
        self.assertEqual(names["worker-beta"]["candidates"], [{"label": "Worker Beta 2", "sources": ["frontiercode"]}])
        self.service.context.assert_not_called()

    async def test_doctor_checks_routes_before_any_launch(self):
        ready = self.pipeline.status()
        self.assertEqual((ready["status"], ready["setup_gaps"]), ("requires_host_receipt", []))
        self.assertEqual(ready["route_checks"]["problems"], [])
        self.assertTrue(all(r["definition"] == "ready" and r["in_inventory"] for r in ready["route_checks"]["routes"]))
        self.assertEqual(ready["route_checks"]["baseline"]["expressible_profiles"], ["general-purpose"])
        self.assertEqual(ready["adapter_capabilities"]["per_call_model"], ["fable", "haiku", "opus", "sonnet"])
        self.assertFalse(ready["adapter_capabilities"]["per_call_effort"])
        # A variant outside the inventory, an alias effort nobody generated and an
        # exempt type whose baseline pins a full ID the Agent call cannot carry.
        self.config["pipeline"]["variants"] += [{"profile": "general-purpose", "model": "sonnet", "effort": "low"}]
        self.config["pipeline"].update(profiles=["general-purpose"], unrouted_agents=["Explore"])
        self.config["inventory"]["available"] = AVAILABLE + [{"model": "opus", "efforts": ["max"]}]
        self.path.write_text(json.dumps(self.config), encoding="utf-8")
        self.config = load_config(self.path)
        self.pipeline = RoutingPipeline(self.make_service())
        problems = {(p["code"], p["route"]) for p in self.pipeline.status()["route_checks"]["problems"]}
        self.assertEqual(problems, {("variant_not_generated", "general-purpose sonnet/low"),
                                    ("route_not_in_inventory", "general-purpose sonnet/low"),
                                    ("variant_not_generated", "general-purpose opus/max"),
                                    ("unrouted_model_not_accepted_per_call", "Explore")})
        self.service.context.assert_not_called()

    async def test_restart_restores_only_host_owned_private_envelope(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        private = self.private_input(prepared["decision_id"])
        self.service = self.make_service()
        self.pipeline = RoutingPipeline(self.service)
        self.submit(prepared["decision_id"], private["result_contract"])
        self.event("PostToolUse", tool_name="Agent", tool_use_id="call-a", tool_response={"status": "completed", "content": []})
        self.assertEqual(self.decision(prepared["decision_id"])["status"], "decided")
        self.service.context.assert_not_called()

    async def test_submissions_are_idempotent_and_conflicts_rejected(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        answer = self.private_input(prepared["decision_id"])["result_contract"]
        self.assertEqual(self.submit(prepared["decision_id"], answer), self.submit(prepared["decision_id"], answer))
        changed = copy.deepcopy(answer)
        changed["rankings"][0]["ranking"].reverse()
        with self.assertRaisesRegex(EvidenceError, "conflicting"):
            self.submit(prepared["decision_id"], changed)

    async def test_numeric_confidence_rejected_even_with_valid_identity(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        answer = self.private_input(prepared["decision_id"])["result_contract"]
        answer["rankings"][0]["confidence"] = 0.9
        self.submit(prepared["decision_id"], answer)
        self.event("SubagentStop", agent="advisor-a")
        self.event("PostToolUse", tool_name="Agent", tool_use_id="call-a", tool_response={"status": "completed", "content": []})
        # The advice is discarded; only the configured baseline remains.
        self.assert_fallback(self.decision(prepared["decision_id"]), "invalid_advisor_result")

    async def test_retry_requires_host_observed_failure(self):
        decision = await self.decided()
        worker = self.authorize(decision)
        with self.assertRaises(EvidenceError):
            self.authorize(decision, retry_of=worker["attempt_id"])
        self.launch(worker, agent="worker-a", tool_id="w")
        self.event("PostToolUseFailure", tool_name="Agent", tool_use_id="w")
        retry = self.authorize(decision, retry_of=worker["attempt_id"])
        self.assertNotEqual(retry["attempt_id"], worker["attempt_id"])
        with self.assertRaises(EvidenceError):
            self.authorize(decision, retry_of=worker["attempt_id"])

    async def test_registered_resume_and_outcome_survive_snapshot_expiry(self):
        decision = await self.decided()
        worker = self.authorize(decision)
        self.launch(worker, agent="worker-a", tool_id="w")
        self.event("SubagentStop", agent="worker-a")
        self.now += 601
        resumed = self.authorize(decision, resume_agent_id="worker-a")
        self.assertEqual(resumed["input"]["resume"], "worker-a")
        self.assertEqual(self.dispatched(resumed, "resume-w")["resume"], "worker-a")
        args = self.rpc("record_routing_outcome", {"decision_id": decision, "execution": {}})
        with patch.object(self.service, "record_routing_outcome", return_value={"recorded": False}) as record:
            self.pipeline.outcome(args)
            record.assert_called_once()
        with self.assertRaises(EvidenceError):
            self.authorize(decision, resume_agent_id="other-worker")

    async def test_each_packet_gets_a_distinct_attempt_even_when_prompts_match(self):
        packets = [PACKETS[0], {**PACKETS[0], "packet_id": "other"}]
        request = {"profile": "general-purpose", "prompt": "same bounded work"}
        prepared = await self.prepare(packets=packets, launch_requests={"work": request, "other": request})
        self.launch(prepared["handoff"])
        self.submit(prepared["decision_id"], self.private_input(prepared["decision_id"])["result_contract"])
        self.event("SubagentStop", agent="advisor-a")
        self.event("PostToolUse", tool_name="Agent", tool_use_id="call-a", tool_response={"status": "completed", "content": []})
        first = self.authorize(prepared["decision_id"])
        second = self.pipeline.authorize(self.rpc("authorize_routing_launch", {"decision_id": prepared["decision_id"], "packet_id": "other"}))
        self.assertNotEqual(first["input"], second["input"])
        self.launch(first, agent="worker-a", tool_id="w1")
        self.launch(second, agent="worker-b", tool_id="w2")

    async def test_session_end_removes_all_session_state(self):
        await self.decided()
        self.event("SessionEnd")
        with self.pipeline.store.transaction() as tx:
            for kind in ("decision", "attempt", "agent", "receipt", "session"):
                self.assertEqual(tx.values(kind), [])

    async def test_doctor_does_not_claim_native_discovery_or_observed_model(self):
        status = self.pipeline.status()
        self.assertFalse(status["guard_installed_verified"])
        self.assertFalse(status["discovery_verified"])
        self.assertIsNone(status["runtime_model_observed"])
        self.service.context.assert_not_called()

    async def test_offline_and_unsupported_host_cannot_dispatch(self):
        self.service.offline = True
        with self.assertRaisesRegex(EvidenceError, "offline"):
            await self.prepare()
        self.service.offline = False
        self.service.client = "codex"
        with self.assertRaisesRegex(EvidenceError, "adapter"):
            await self.prepare()

    async def test_hook_subprocess_stamps_receipt_consumable_in_other_process(self):
        event = {"hook_event_name": "PreToolUse", "session_id": "session-a",
                 "tool_name": "mcp__assay-benchmark-routing__get_routing_decision",
                 "tool_input": {"decision_id": "missing"}}
        proc = subprocess.run([sys.executable, "-I", "-B", str(SCRIPTS / "routing_hook.py")],
            env={**os.environ, "ASSAY_ROUTING_CONFIG": str(self.path)}, input=json.dumps(event),
            text=True, capture_output=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        supplied = json.loads(proc.stdout)["hookSpecificOutput"]["updatedInput"]
        host = self.pipeline.host("get_routing_decision", supplied)
        self.assertEqual(host["session_id"], "session-a")

    async def test_bad_hook_input_fails_closed_without_echo(self):
        proc = subprocess.run([sys.executable, "-I", "-B", str(SCRIPTS / "routing_hook.py")],
            input="PRIVATE_SENTINEL", text=True, capture_output=True, timeout=10)
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("PRIVATE_SENTINEL", proc.stderr + proc.stdout)
        # A routed definition's own hook never stalls its ordinary tools.
        proc = subprocess.run([sys.executable, "-I", "-B", str(SCRIPTS / "routing_hook.py"), "--scope", "agent"],
            input="PRIVATE_SENTINEL", text=True, capture_output=True, timeout=10)
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, "{}"))

    async def test_stop_without_return_does_not_authorize_or_cache_advice(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        self.submit(prepared["decision_id"], self.private_input(prepared["decision_id"])["result_contract"])
        self.event("SubagentStop", agent="advisor-a")
        self.assertEqual(self.decision(prepared["decision_id"])["status"], "awaiting_advisor_completion")
        with self.assertRaisesRegex(EvidenceError, "completion_not_observed"):
            self.authorize(prepared["decision_id"])
        self.assertFalse(self.service.advisor_workflow._cache)

    async def test_observed_model_mismatch_cannot_authorize_or_seed_cache(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        self.submit(prepared["decision_id"], self.private_input(prepared["decision_id"])["result_contract"])
        self.event("PostToolUse", tool_name="Agent", tool_use_id="call-a", tool_response={
            "status": "completed", "agentId": "advisor-a", "resolvedModel": "different-model", "content": []})
        self.assertEqual(self.decision(prepared["decision_id"])["status"], "no_decision")
        self.assertFalse(self.service.advisor_workflow._cache)
        with self.assertRaisesRegex(EvidenceError, "no_executable_decision"):
            self.authorize(prepared["decision_id"])

    async def test_advisor_result_redaction_preserves_native_shape_and_observed_model(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        self.submit(prepared["decision_id"], self.private_input(prepared["decision_id"])["result_contract"])
        raw = completed_output(resolvedModel=ROUTE["model"], modelsUsed=[ROUTE["model"]])
        event = self.event("PostToolUse", tool_name="Agent", tool_use_id="call-a", tool_response=raw)
        safe = event["hookSpecificOutput"]["updatedToolOutput"]
        assert_agent_output(self, safe)
        self.assertEqual(safe["totalTokens"], 42)
        self.assertNotIn("PRIVATE_", json.dumps(safe))
        self.assertEqual(raw["usage"]["input_tokens"], safe["usage"]["input_tokens"])
        self.assertEqual(self.decision(prepared["decision_id"])["advisor_provenance"]["observed_model"], ROUTE["model"])

    async def test_private_advisor_requires_native_background_protection_before_reserving(self):
        prepared = await self.prepare()
        launch = prepared["handoff"]
        event = {"hook_event_name": "PreToolUse", "session_id": "session-a", "tool_name": "Agent",
                 "tool_use_id": "call-a", "tool_input": launch["input"]}
        for environment in ({}, {"CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "0"}):
            result = handle(event, self.config, clock=lambda: self.now, environment=environment)
            self.assertEqual("deny", result["hookSpecificOutput"]["permissionDecision"])
            self.assertNotIn("updatedInput", result["hookSpecificOutput"])
            with self.pipeline.store.transaction() as tx:
                self.assertEqual("prepared", tx.get("attempt", launch["attempt_id"])["state"])
        self.assertFalse(self.dispatched(launch, "call-a")["run_in_background"])

    async def test_advisor_handback_is_status_only_and_no_submission_is_forged(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        event = self.event("PreToolUse", agent="advisor-a", tool_name="SubagentHandback",
            tool_input={"message": "RAW_BENCHMARK_SENTINEL", "summary": "SECOND_SENTINEL"})
        safe = event["hookSpecificOutput"]["updatedInput"]
        self.assertNotIn("SENTINEL", json.dumps(safe))
        self.assertEqual(json.loads(safe["message"])["status"], "not_submitted")

    async def test_model_switch_is_detected_even_if_final_model_matches(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        self.submit(prepared["decision_id"], self.private_input(prepared["decision_id"])["result_contract"])
        self.event("PostToolUse", tool_name="Agent", tool_use_id="call-a", tool_response={
            "status": "completed", "resolvedModel": ROUTE["model"],
            "modelsUsed": [ROUTE["model"], "other-model"], "content": []})
        self.assertEqual(self.decision(prepared["decision_id"])["status"], "no_decision")

    async def test_approved_choice_applies_when_root_omits_explicit_and_advisor_file_is_absent(self):
        pair = {"model": "worker-alpha", "effort": "high"}
        self.config["pipeline"]["approved_choices"] = {"work": pair}
        self.configure()
        advisor = resolve_variant(settings(self.config), "routing-advisor", ROUTE, environment={})
        (self.root / "agents" / advisor["file"]).unlink()
        prepared = await self.prepare()
        self.assertNotIn("handoff", prepared)
        self.assertEqual({k: prepared["decisions"][0]["selected"][k] for k in pair}, pair)
        self.assertEqual(self.authorize(prepared["decision_id"])["requested_effort"], "high")

    async def test_hard_capability_uses_configured_profile_observation_only(self):
        packets = [{**PACKETS[0], "requirements": {"capabilities": ["shell"]}}]
        absent = await self.prepare(packets=packets)
        self.assertEqual(absent["status"], "no_decision")
        self.config["pipeline"]["profile_capabilities"] = {"general-purpose": {"shell": True}}
        self.configure()
        supported = await self.prepare(packets=packets)
        self.assertEqual(supported["status"], "awaiting_native_advice")

    async def test_preparation_preserves_inventory_observation_time_and_remaining_ttl(self):
        self.now += 86390
        self.event("SessionStart")
        prepared = await self.prepare()
        from route_evidence.core import epoch
        self.assertLessEqual(epoch(prepared["expires_at"]), self.now + 10.001)
        self.assertEqual(self.service._inventory["observed_at"], self.config["inventory"]["observed_at"])

    async def test_raw_attempt_prompt_is_removed_after_start(self):
        decision = await self.decided()
        launch = self.authorize(decision)
        self.launch(launch, agent="worker-a", tool_id="w")
        with self.pipeline.store.transaction() as tx:
            for kind in ("attempt", "agent"):
                self.assertNotIn("PRIVATE_WORK_PROMPT", json.dumps(tx.values(kind)))

    async def test_late_background_post_does_not_reopen_finished_worker(self):
        self.config["pipeline"]["approved_choices"] = {"work": {"model": "worker-alpha", "effort": "low"}}
        self.configure()
        prepared = await self.prepare(launch_requests={"work": {"profile": "general-purpose", "prompt": "bounded", "run_in_background": True}})
        worker = self.authorize(prepared["decision_id"])
        self.launch(worker, agent="worker-a", tool_id="w")
        self.event("SubagentStop", agent="worker-a")
        self.event("PostToolUse", tool_name="Agent", tool_use_id="w", tool_response={"status": "async_launched", "agentId": "worker-a"})
        with self.pipeline.store.transaction() as tx:
            self.assertEqual(tx.get("attempt", worker["attempt_id"])["state"], "finished")

    async def test_absent_evidence_only_and_other_host_configurations_are_inert(self):
        launch = {"hook_event_name": "PreToolUse", "session_id": "s", "tool_name": "Agent",
                  "tool_use_id": "t", "tool_input": {"subagent_type": "Explore", "prompt": "find"}}
        start = {"hook_event_name": "SessionStart", "session_id": "s", "source": "startup"}
        for config in ({}, {"schema_version": 1, "client": "claude"},
                       {"schema_version": 3, "client": "claude"},
                       {"schema_version": 3, "client": "claude", "pipeline": {"mode": "evidence-only"}},
                       {**self.config, "client": "codex"}):
            with self.subTest(config=config):
                self.assertEqual(handle(launch, config), {})
                self.assertEqual(handle(start, config), {})
                self.assertEqual(handle({**launch, "tool_name": "spawn_agent"}, config), {})

    async def test_exempt_agent_types_launch_with_their_configured_model(self):
        self.config["pipeline"]["unrouted_agents"] = {"Explore": {"model": "haiku"}, "Plan": "inherit",
                                                      "claude-code-guide": "baseline"}
        self.configure()
        def launch(agent_type, agent=None, **fields):
            return self.event("PreToolUse", agent=agent, tool_name="Agent", tool_use_id="t-" + agent_type,
                              tool_input={"subagent_type": agent_type, "prompt": "bounded", **fields})
        # Only the model is added; every other field, the background flag included, stays the caller's.
        explore = launch("Explore", run_in_background=True)["hookSpecificOutput"]
        self.assertNotIn("permissionDecision", explore)
        self.assertEqual(explore["updatedInput"], {"subagent_type": "Explore", "prompt": "bounded",
                                                   "run_in_background": True, "model": "haiku"})
        self.assertEqual(launch("Explore", model="haiku"), {})
        refused = launch("Explore", model="opus")["hookSpecificOutput"]
        self.assertIn("prepare_routing", refused["permissionDecisionReason"])
        self.assertEqual(launch("Plan"), {})  # only an explicit inherit keeps the parent's model
        # This baseline pins a full ID, which an Agent call cannot carry.
        self.assertIn("unrouted_model_not_accepted_per_call",
                      launch("claude-code-guide")["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertEqual(launch("general-purpose")["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(launch("Explore", agent="worker-x")["hookSpecificOutput"]["permissionDecision"], "deny")
        # The exempt launch still reports what its alias resolved to.
        self.event("PostToolUse", tool_name="Agent", tool_use_id="t-Explore", tool_input=explore["updatedInput"],
                   tool_response={"status": "completed", "resolvedModel": "fixture-haiku-9", "content": []})
        with self.pipeline.store.transaction() as tx:
            self.assertEqual(tx.get("alias", "haiku")["model"], "fixture-haiku-9")

    async def test_a_listed_exempt_type_uses_the_baseline_model(self):
        self.config["inventory"]["available"] = AVAILABLE + [{"model": "haiku", "efforts": ["low"]}]
        self.config["pipeline"].update(unrouted_agents=["Explore"], baseline={"model": "haiku", "effort": "low"})
        self.configure()
        reply = self.event("PreToolUse", tool_name="Agent", tool_use_id="t",
                           tool_input={"subagent_type": "Explore", "prompt": "find"})
        self.assertEqual(reply["hookSpecificOutput"]["updatedInput"]["model"], "haiku")

    async def test_parallel_launches_of_one_definition_start_and_results_fix_attribution(self):
        pair = {"model": "worker-alpha", "effort": "low"}
        self.config["pipeline"]["approved_choices"] = {"p1": pair, "p2": pair}
        self.configure()
        packets = [{**PACKETS[0], "packet_id": p} for p in ("p1", "p2")]
        requests = {p: {"profile": "general-purpose", "prompt": "bounded work " + p} for p in ("p1", "p2")}
        prepared = await self.prepare(packets=packets, launch_requests=requests)
        first, second = (self.pipeline.authorize(self.rpc("authorize_routing_launch", {
            "decision_id": prepared["decision_id"], "packet_id": p})) for p in ("p1", "p2"))
        name = first["input"]["subagent_type"]
        self.assertEqual(name, second["input"]["subagent_type"])
        # One assistant message: both calls pass before either native start event.
        self.assertIn("bounded work p1", self.dispatched(first, "c1")["prompt"])
        self.now += 1
        self.assertIn("bounded work p2", self.dispatched(second, "c2")["prompt"])
        # The host starts the later call first; start order binds provisionally
        # and the Agent result, which names both IDs, corrects the attribution.
        self.event("SubagentStart", agent="agent-2", agent_type=name)
        self.event("SubagentStart", agent="agent-1", agent_type=name)
        self.event("PostToolUse", tool_name="Agent", tool_use_id="c2", tool_response={"status": "async_launched", "agentId": "agent-2"})
        self.event("PostToolUse", tool_name="Agent", tool_use_id="c1", tool_response={"status": "async_launched", "agentId": "agent-1"})
        with self.pipeline.store.transaction() as tx:
            self.assertEqual(tx.get("attempt", first["attempt_id"])["agent_id"], "agent-1")
            self.assertEqual(tx.get("attempt", second["attempt_id"])["agent_id"], "agent-2")
            self.assertEqual(tx.get("agent", "session-a:agent-1")["packet_id"], "p1")
            self.assertEqual(tx.get("agent", "session-a:agent-2")["packet_id"], "p2")

    async def test_result_before_sibling_start_leaves_the_sibling_awaiting_its_own_start(self):
        pair = {"model": "worker-alpha", "effort": "low"}
        self.config["pipeline"]["approved_choices"] = {"p1": pair, "p2": pair}
        self.configure()
        packets = [{**PACKETS[0], "packet_id": p} for p in ("p1", "p2")]
        requests = {p: {"profile": "general-purpose", "prompt": "work " + p, "run_in_background": True} for p in ("p1", "p2")}
        prepared = await self.prepare(packets=packets, launch_requests=requests)
        first, second = (self.pipeline.authorize(self.rpc("authorize_routing_launch", {
            "decision_id": prepared["decision_id"], "packet_id": p})) for p in ("p1", "p2"))
        self.dispatched(first, "c1")
        self.now += 1
        self.dispatched(second, "c2")
        self.event("SubagentStart", agent="agent-2", agent_type=second["input"]["subagent_type"])
        self.event("PostToolUse", tool_name="Agent", tool_use_id="c2", tool_response={"status": "async_launched", "agentId": "agent-2"})
        with self.pipeline.store.transaction() as tx:
            self.assertEqual(tx.get("attempt", second["attempt_id"])["agent_id"], "agent-2")
            self.assertEqual(tx.get("attempt", first["attempt_id"])["state"], "reserved")
            self.assertNotIn("agent_id", tx.get("attempt", first["attempt_id"]))
        self.event("SubagentStart", agent="agent-1", agent_type=first["input"]["subagent_type"])
        with self.pipeline.store.transaction() as tx:
            self.assertEqual(tx.get("attempt", first["attempt_id"])["agent_id"], "agent-1")

    async def test_parallel_same_definition_different_models_are_not_prejudged(self):
        self.use_aliases(approved_choices={"p1":{"model":"sonnet","effort":"low"},
                                          "p2":{"model":"haiku","effort":"low"}})
        packets=[{**PACKETS[0],"packet_id":p} for p in ("p1","p2")]
        prepared=await self.prepare(packets=packets,launch_requests={
            p:{"profile":"general-purpose","prompt":"bounded "+p} for p in ("p1","p2")})
        first,second=(self.pipeline.authorize(self.rpc("authorize_routing_launch",{
            "decision_id":prepared["decision_id"],"packet_id":p})) for p in ("p1","p2"))
        self.dispatched(first,"c1"); self.now+=1; self.dispatched(second,"c2")
        name=first["input"]["subagent_type"]
        self.assertEqual(name,second["input"]["subagent_type"])
        self.event("SubagentStart",agent="agent-2",agent_type=name)
        self.event("SubagentStart",agent="agent-1",agent_type=name)
        # Wrong effort on agent-2 must follow that agent, not its provisional
        # packet association. Both starts remain ambiguous until native returns.
        self.event("SubagentStop",agent="agent-2",effort={"level":"high"})
        self.event("SubagentStop",agent="agent-1",effort={"level":"low"})
        with self.pipeline.store.transaction() as tx:
            for launch in (first,second):
                provisional=tx.get("attempt",launch["attempt_id"])
                self.assertEqual("start_order",provisional["binding"])
                self.assertNotIn("route_mismatch",provisional)
        self.returned("c2","agent-2","haiku-resolved",modelsUsed=["haiku-resolved"])
        self.returned("c1","agent-1","sonnet-resolved",modelsUsed=["sonnet-resolved"])
        with self.pipeline.store.transaction() as tx:
            one,two=(tx.get("attempt",l["attempt_id"]) for l in (first,second))
            self.assertEqual(("agent-1","sonnet-resolved","low"),(one["agent_id"],one["observed_model"],one["observed_effort"]))
            self.assertNotIn("route_mismatch",one)
            self.assertTrue(two["route_mismatch"])
            self.assertEqual("host_result",two["binding"])

    async def test_unknown_advisor_envelopes_cannot_add_report_channels(self):
        prepared=await self.prepare()
        self.launch(prepared["handoff"])
        event=self.event("PostToolUse",tool_name="Agent",tool_use_id="call-a",tool_response={
            "status":"completed","agentId":"advisor-a","report":{"text":"PRIVATE_SENTINEL"},
            "error":"PRIVATE_SENTINEL", "summary":"PRIVATE_SENTINEL"})
        safe=event["hookSpecificOutput"]["updatedToolOutput"]
        assert_agent_output(self, safe)
        self.assertNotIn("PRIVATE_SENTINEL",json.dumps(safe))

    async def test_later_return_does_not_clear_prior_model_switch(self):
        self.use_aliases(approved_choices={"work":{"model":"sonnet","effort":"low"}})
        prepared=await self.prepare()
        worker=self.authorize(prepared["decision_id"])
        self.launch(worker,agent="worker-a",tool_id="w")
        self.returned("w","worker-a","resolved-sonnet",modelsUsed=["other-model","resolved-sonnet"])
        self.returned("w","worker-a","resolved-sonnet",modelsUsed=["resolved-sonnet"])
        self.returned("w","worker-a","resolved-sonnet")
        with self.pipeline.store.transaction() as tx:
            self.assertTrue(tx.get("attempt",worker["attempt_id"])["route_mismatch"])

    async def test_custom_effort_field_is_denied_even_on_exempt_agent(self):
        self.use_aliases(unrouted_agents={"Explore":{"model":"haiku"}})
        for field in ("effort","model_reasoning_effort","reasoning_effort"):
            event=self.event("PreToolUse",tool_name="Agent",tool_input={
                "subagent_type":"Explore","prompt":"find",field:"low"})
            self.assertEqual("deny",event["hookSpecificOutput"]["permissionDecision"])

    async def test_exempt_model_checks_versioned_environment_override(self):
        self.use_aliases(unrouted_agents={"Explore":{"model":"haiku"}})
        event={"hook_event_name":"PreToolUse","tool_name":"Agent","tool_input":{
            "subagent_type":"Explore","prompt":"find","run_in_background":True}}
        env={"CLAUDE_CODE_SUBAGENT_MODEL":"opus"}
        result=handle(event,self.config,environment=env)
        self.assertEqual("deny",result["hookSpecificOutput"]["permissionDecision"])
        self.config["pipeline"]["host"]={"surface":"cli","version":"2.1.251"}
        result=handle(event,self.config,environment=env)
        self.assertEqual("haiku",result["hookSpecificOutput"]["updatedInput"]["model"])
        self.assertTrue(result["hookSpecificOutput"]["updatedInput"]["run_in_background"])
        self.assertNotIn("permissionDecision",result["hookSpecificOutput"])

    async def test_auto_mode_denial_releases_a_reserved_launch(self):
        decision = await self.decided()
        worker = self.authorize(decision)
        self.dispatched(worker, "denied-call")
        self.assertEqual("deny", self.event("PreToolUse", tool_name="Agent", tool_use_id="retry-call",
            tool_input=worker["input"])["hookSpecificOutput"]["permissionDecision"])
        self.event("PermissionDenied", tool_name="Agent", tool_use_id="denied-call", tool_input=worker["input"], reason="[rule]")
        self.launch(worker, agent="worker-a", tool_id="retry-call")
        with self.pipeline.store.transaction() as tx:
            attempt = tx.get("attempt", worker["attempt_id"])
            self.assertEqual((attempt["tool_use_id"], attempt["agent_id"]), ("retry-call", "worker-a"))

    def use_aliases(self, **pipeline):
        """Per-call routing: alias models in the inventory and a routed profile."""
        self.config["inventory"]["available"] = [{"model": "sonnet", "efforts": ["low", "high"]},
                                                 {"model": "haiku", "efforts": ["low"]}]
        self.config["pipeline"].update(profiles=["general-purpose"], variants=[],
                                       advisor_route={**ROUTE, "model": "haiku", "effort": "low"},
                                       baseline={"model": "sonnet", "effort": "low"}, **pipeline)
        self.configure()

    def returned(self, tool_id, agent, resolved, **response):
        self.event("PostToolUse", tool_name="Agent", tool_use_id=tool_id, tool_response={
            "status": "completed", "agentId": agent, "resolvedModel": resolved, "content": [], **response})

    async def test_alias_models_travel_in_the_agent_call(self):
        self.use_aliases()
        prepared = await self.prepare()
        # The advisor's alias is in the stub the root sends and in the substitution.
        self.assertEqual(prepared["handoff"]["input"]["model"], "haiku")
        self.assertEqual(self.launch(prepared["handoff"])["model"], "haiku")
        self.submit(prepared["decision_id"], self.private_input(prepared["decision_id"])["result_contract"])
        self.event("SubagentStop", agent="advisor-a", effort={"level": "low"})
        # The host reports the full ID the alias resolved to; that is not a mismatch.
        self.returned("call-a", "advisor-a", "fixture-haiku-9")
        result = self.decision(prepared["decision_id"])
        self.assertEqual(result["status"], "decided")
        self.assertEqual(result["advisor_provenance"]["observed_model"], "fixture-haiku-9")
        worker = self.authorize(prepared["decision_id"])
        self.assertEqual(worker["input"]["model"], worker["requested_model"])
        self.assertEqual(self.launch(worker, agent="worker-a", tool_id="w")["model"], worker["requested_model"])
        text = (self.root / "agents" / (worker["input"]["subagent_type"] + ".md")).read_text(encoding="utf-8")
        self.assertIn("effort: " + worker["requested_effort"], text)
        self.assertNotIn("\nmodel:", text)

    async def test_a_new_alias_model_needs_no_regeneration(self):
        self.use_aliases()
        before = sorted(p.name for p in (self.root / "agents").iterdir())
        self.config["inventory"]["available"].append({"model": "opus", "efforts": ["high"]})
        self.path.write_text(json.dumps(self.config), encoding="utf-8")
        self.config = load_config(self.path)
        self.service = self.make_service()
        self.pipeline = RoutingPipeline(self.service)
        self.event("SessionStart")
        prepared = await self.prepare(packets=[{**PACKETS[0], "explicit_source": "user",
                                               "explicit": {"model": "opus", "effort": "high"}}])
        self.assertEqual(prepared["decisions"][0]["decision_type"], "explicit_user_choice")
        launch = self.authorize(prepared["decision_id"])
        self.assertEqual((launch["input"]["model"], launch["requested_effort"]), ("opus", "high"))
        self.assertEqual(sorted(p.name for p in (self.root / "agents").iterdir()), before)

    async def test_a_new_alias_resolution_is_an_inventory_event_not_a_mismatch(self):
        pair = {"model": "sonnet", "effort": "low"}
        self.config["pipeline"].update(profiles=["general-purpose"], variants=[], baseline=pair,
                                       advisor_route={**ROUTE, **pair}, approved_choices={"work": pair})
        self.use_inventory_file([{"model": "sonnet", "evidence_names": ["Fixture Sonnet A"], "efforts": ["low"]}])

        async def run(tool_id, agent, resolved):
            prepared = await self.prepare()
            worker = self.authorize(prepared["decision_id"])
            self.launch(worker, agent=agent, tool_id=tool_id)
            self.event("SubagentStop", agent=agent, effort={"level": "low"})
            self.returned(tool_id, agent, resolved)
            with self.pipeline.store.transaction() as tx:
                return prepared, tx.get("attempt", worker["attempt_id"])

        self.now += 1
        first, attempt = await run("w1", "worker-a", "fixture-sonnet-a")
        self.assertNotIn("inventory_warnings", first)
        self.assertFalse(attempt.get("route_mismatch"))
        self.now += 1
        second, attempt = await run("w2", "worker-b", "fixture-sonnet-b")
        self.assertEqual(attempt["alias_changed"], {"from": "fixture-sonnet-a", "to": "fixture-sonnet-b"})
        self.assertFalse(attempt.get("route_mismatch"))
        self.authorize(second["decision_id"], resume_agent_id="worker-b")  # the route still holds
        self.assertFalse(self.pipeline.status()["alias_observations"][0]["change"]["confirmed"])
        # Until the owner confirms the inventory again, the old spelling no longer names the alias.
        self.now += 1
        again = await self.prepare()
        self.assertEqual(again["inventory_warnings"], [{"code": "alias_resolution_changed", "alias": "sonnet",
                                                        "from": "fixture-sonnet-a", "to": "fixture-sonnet-b"}])
        self.assertNotIn("evidence_names", self.service.inventory["available"][0])
        confirm_inventory(self.config, clock=lambda: self.now + 1)
        self.now += 2
        self.assertTrue(self.pipeline.status()["alias_observations"][0]["change"]["confirmed"])
        self.assertNotIn("inventory_warnings", await self.prepare())
        self.assertEqual(self.service.inventory["available"][0]["evidence_names"], ["Fixture Sonnet A"])
        self.event("SessionEnd")
        with self.pipeline.store.transaction() as tx:
            self.assertEqual(tx.get("alias", "sonnet")["model"], "fixture-sonnet-b")  # outlives the session

    async def test_a_model_switch_inside_an_alias_run_is_still_a_mismatch(self):
        pair = {"model": "sonnet", "effort": "low"}
        self.use_aliases(approved_choices={"work": pair})
        worker = self.authorize((await self.prepare())["decision_id"])
        self.launch(worker, agent="worker-a", tool_id="w")
        self.returned("w", "worker-a", "fixture-sonnet-a", modelsUsed=["fixture-sonnet-a", "fixture-other"])
        with self.pipeline.store.transaction() as tx:
            self.assertTrue(tx.get("attempt", worker["attempt_id"])["route_mismatch"])

    def use_inventory_file(self, available=None, **pipeline):
        location = self.root / "inventory.json"
        location.write_text(json.dumps({"available": available or AVAILABLE, "observed_at": timestamp(self.now)}),
                            encoding="utf-8")
        self.config.pop("inventory", None)
        self.config["pipeline"].update(inventory_file=str(location), **pipeline)
        self.configure()

    async def test_confirmed_inventory_file_renews_preparation_without_reconnect(self):
        self.use_inventory_file(inventory_ttl_hours=1)
        await self.prepare()
        self.now += 2 * 3600
        with self.assertRaisesRegex(EvidenceError, "inventory_expired"):
            await self.prepare()
        report = confirm_inventory(self.config, clock=lambda: self.now)
        self.assertFalse(report["configuration_changed"])
        # Same session registration and server: no reconnect, no restart.
        prepared = await self.prepare()
        self.assertEqual(prepared["status"], "awaiting_native_advice")

    async def test_confirmed_spelling_binds_only_through_the_inventory_file(self):
        self.use_inventory_file()
        location = Path(self.config["pipeline"]["inventory_file"])
        before = location.read_bytes()
        for names, error in (([("unlisted-model", "Unlisted 1")], "not_in_inventory"),
                             ([("worker-alpha", "Shared Label"), ("worker-beta", "Shared Label")], "ambiguous")):
            with self.subTest(error=error), self.assertRaisesRegex(EvidenceError, error):
                confirm_inventory(self.config, evidence_names=names, clock=lambda: self.now)
            self.assertEqual(location.read_bytes(), before)
        cache = self.root / "empty-cache"
        proc = subprocess.run([sys.executable, "-B", str(SCRIPTS / "benchmark_router.py"), "--cache-dir", str(cache),
                               "--config", str(self.path), "inventory-confirm",
                               "--evidence-name", "worker-alpha=Worker Alpha 2", "--evidence-name", "worker-alpha=Worker Alpha 2"],
                              env={k: v for k, v in os.environ.items() if k != "ASSAY_ROUTING_CONFIG"},
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = json.loads(proc.stdout)
        self.assertFalse(report["configuration_changed"])
        self.assertEqual(report["model_names"]["status"], "no_cached_rows")
        recorded = json.loads(location.read_text(encoding="utf-8"))["available"]
        self.assertEqual(recorded[0], {**AVAILABLE[0], "evidence_names": ["Worker Alpha 2"]})
        self.assertEqual(recorded[1], AVAILABLE[1])

    async def test_inline_and_file_inventory_together_are_refused(self):
        location = self.root / "inventory.json"
        location.write_text(json.dumps({"available": AVAILABLE, "observed_at": timestamp(self.now)}), encoding="utf-8")
        both = {**self.config, "pipeline": {**self.config["pipeline"], "inventory_file": str(location)}}
        with self.assertRaisesRegex(EvidenceError, "configured_twice"):
            configured_inventory(both)

    async def test_inventory_lifetime_follows_the_configured_ttl(self):
        self.use_inventory_file(inventory_ttl_hours=3)
        self.now += 2 * 3600
        await self.prepare()
        self.now += 1.5 * 3600
        with self.assertRaisesRegex(EvidenceError, "inventory_expired"):
            await self.prepare()

    async def test_worker_effort_is_checked_after_the_run_not_during_it(self):
        decision = await self.decided()
        worker = self.authorize(decision)
        self.launch(worker, agent="worker-a", tool_id="w")
        read = dict(agent="worker-a", tool_name="Read", tool_input={"file_path": "x"}, effort={"level": "max"})
        # Neither hook stops a worker midway, which would leave partial changes.
        self.assertEqual(self.event("PreToolUse", **read), {})
        self.assertEqual(self.event("PreToolUse", scope="agent", **read), {})
        # The stop event reports the effort the host applied; a different one
        # blocks continuing that worker.
        self.event("SubagentStop", agent="worker-a", effort={"level": "max"})
        with self.assertRaisesRegex(EvidenceError, "route_mismatch"):
            self.authorize(decision, resume_agent_id="worker-a")

    def run_hook(self, event, *args, config):
        env = {**os.environ, "ASSAY_ROUTING_CONFIG": str(config)}
        proc = subprocess.run([sys.executable, "-I", "-B", str(SCRIPTS / "routing_hook.py"), *args],
            env=env, input=json.dumps(event).encode(), capture_output=True, timeout=10)
        return proc.returncode, proc.stdout

    async def test_configuration_failure_blocks_only_launches_and_routing_calls(self):
        broken = self.root / "broken.json"
        broken.write_text("{not json", encoding="utf-8")
        base = {"session_id": "session-a", "tool_use_id": "t", "tool_input": {}}
        for config in (broken, self.root / "missing.json"):
            for event, args, expected in (
                ({"hook_event_name": "PreToolUse", "tool_name": "Agent", **base}, (), "deny"),
                ({"hook_event_name": "PreToolUse", "tool_name": "mcp__assay-benchmark-routing__prepare_routing", **base}, (), "deny"),
                ({"hook_event_name": "PreToolUse", "tool_name": "Read", "agent_id": "a", **base}, ("--scope", "agent"), None),
                ({"hook_event_name": "SubagentStop", "agent_id": "a", "agent_type": "assay-x", "session_id": "session-a"}, (), None),
                ({"hook_event_name": "PostToolUse", "tool_name": "Agent", **base}, (), "redact"),
            ):
                with self.subTest(config=config.name, event=event["hook_event_name"], tool=event.get("tool_name")):
                    code, stdout = self.run_hook(event, *args, config=config)
                    self.assertEqual(code, 0)
                    reply = json.loads(stdout)
                    if expected is None:
                        self.assertEqual(reply, {})
                    elif expected == "redact":
                        assert_agent_output(self, reply["hookSpecificOutput"]["updatedToolOutput"])
                    else:
                        self.assertEqual(reply["hookSpecificOutput"]["permissionDecision"], expected)

    async def test_unexpected_guard_error_on_a_launch_is_a_denial(self):
        import contextlib
        import io
        from types import SimpleNamespace
        import routing_hook
        event = {"hook_event_name": "PreToolUse", "session_id": "s", "tool_name": "Agent", "tool_use_id": "t", "tool_input": {}}
        for scope, expected in (([], "deny"), (["--scope", "agent"], None)):
            out = io.StringIO()
            with (patch.object(routing_hook, "handle", side_effect=KeyError("unexpected")),
                  patch.object(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(json.dumps(event).encode()))),
                  contextlib.redirect_stdout(out)):
                self.assertEqual(routing_hook.main(scope), 0)
            reply = json.loads(out.getvalue())
            self.assertEqual(reply.get("hookSpecificOutput", {}).get("permissionDecision"), expected)

    async def test_substituted_prompt_keeps_any_script_in_ascii_hook_output(self):
        self.config["pipeline"]["approved_choices"] = {"work": {"model": "worker-alpha", "effort": "low"}}
        self.configure()
        prompt = "Проверь ограниченный пакет и верни доказательства. 検証"
        prepared = await self.prepare(launch_requests={"work": {"profile": "general-purpose", "prompt": prompt}})
        worker = self.authorize(prepared["decision_id"])
        event = {"hook_event_name": "PreToolUse", "session_id": "session-a", "tool_name": "Agent",
                 "tool_use_id": "w", "tool_input": worker["input"]}
        code, stdout = self.run_hook(event, config=self.path)
        self.assertEqual(code, 0)
        stdout.decode("ascii")
        self.assertIn(prompt, json.loads(stdout)["hookSpecificOutput"]["updatedInput"]["prompt"])


if __name__ == "__main__":
    unittest.main()
