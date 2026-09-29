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
from route_evidence.claude_agents import generate, resolve_variant
from route_evidence.core import EvidenceError, timestamp
from route_evidence.pipeline import RoutingPipeline
from route_evidence.pipeline_config import settings
from route_evidence.pipeline_store import PipelineStore
from route_evidence.routing import build_context
from route_evidence.service import RoutingService, load_config
from routing_hook import handle

AVAILABLE = [{"model": "worker-alpha", "efforts": ["low", "high"]},
             {"model": "worker-beta", "efforts": ["medium"]}]
ROUTE = {"model": "worker-beta", "effort": "medium",
         "selection_basis": {"source": "client_role", "reason_code": "bounded_ranking"}}
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
            "pipeline": {"state_dir": str(self.root / "state"), "agents_dir": str(self.root / "agents"),
                "advisor_route": ROUTE,
                "variants": [{"profile": "general-purpose", "model": m["model"], "effort": e}
                             for m in AVAILABLE for e in m["efforts"]]}}
        self.configure()

    def configure(self):
        self.path.write_text(json.dumps(self.config), encoding="utf-8")
        self.config = load_config(self.path)
        generate(settings(self.config), {})
        self.service = self.make_service()
        self.pipeline = RoutingPipeline(self.service)
        self.event("SessionStart")

    def make_service(self):
        service = RoutingService(Cache(self.root / "cache", clock=lambda: self.now),
            client="claude", clock=lambda: self.now, advisor_config=self.config,
            inventory=self.config["inventory"])
        async def context(request):
            return {**build_context(request, []), "sources": [], "data_status": "unavailable",
                    "data_message": "synthetic-only", "usage": "routing"}
        service.context = AsyncMock(side_effect=context)
        return service

    def event(self, name, *, agent=None, session="session-a", **fields):
        event = {"hook_event_name": name, "session_id": session, **fields}
        if agent is not None:
            event["agent_id"] = agent
        return handle(event, self.config, clock=lambda: self.now, environment={})

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

    def launch(self, launch, *, agent="advisor-a", tool_id="call-a", **fields):
        self.assertEqual({}, self.event("PreToolUse", tool_name="Agent", tool_use_id=tool_id,
            tool_input=launch["input"]))
        self.event("SubagentStart", agent=agent, agent_type=launch["input"]["subagent_type"], **fields)

    def private_input(self, decision_id, agent="advisor-a"):
        return self.pipeline.advisor_input(self.rpc("get_advisor_input", {"decision_id": decision_id}, agent=agent, effort={"level": "medium"}))

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
        self.assertIn("PRIVATE_WORK_PROMPT", worker["input"]["prompt"])
        self.launch(worker, agent="worker-a", tool_id="call-worker")

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

    async def test_uncertified_user_choice_and_fallback_are_rejected(self):
        for key in ("explicit", "baseline"):
            with self.subTest(key=key), self.assertRaisesRegex(EvidenceError, "authority"):
                await self.prepare(packets=[{**PACKETS[0], key: {"model": "worker-alpha", "effort": "high"}}])

    async def test_configured_choice_skips_advisor_but_still_gates_dispatch(self):
        pair = {"model": "worker-alpha", "effort": "high"}
        self.config["pipeline"]["approved_choices"] = {"work": pair}
        self.configure()
        with patch("route_evidence.advisors.native.prepare_native", side_effect=AssertionError("must skip")):
            prepared = await self.prepare(packets=[{**PACKETS[0], "explicit": pair}])
        self.assertNotIn("handoff", prepared)
        self.assertEqual(prepared["decisions"][0]["decision_type"], "explicit_user_choice")
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

    async def test_advisor_cannot_use_other_tools_or_recurse(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        for tool in ("Bash", "Read", "Agent", "mcp__assay-benchmark-routing__prepare_routing"):
            with self.subTest(tool=tool):
                reply = self.event("PreToolUse", agent="advisor-a", tool_name=tool, tool_input={})
                self.assertEqual(reply["hookSpecificOutput"]["permissionDecision"], "deny")

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
        self.assertEqual({}, self.event("PreToolUse", **event))
        self.assertEqual({}, self.event("PreToolUse", **event))
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

    async def test_failed_advisor_uses_only_configured_baseline(self):
        self.config["pipeline"]["baseline"] = {"model": "worker-alpha", "effort": "low"}
        self.configure()
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        self.event("PostToolUseFailure", tool_name="Agent", tool_use_id="call-a")
        result = self.decision(prepared["decision_id"])
        self.assertEqual(result["status"], "decided")
        self.assertEqual(result["decisions"][0]["selected"]["model"], "worker-alpha")
        self.assertNotIn('"ranking"', json.dumps(result))

    async def test_finished_advisor_without_baseline_does_not_inherit_parent(self):
        prepared = await self.prepare()
        self.launch(prepared["handoff"])
        self.event("SubagentStop", agent="advisor-a")
        self.event("PostToolUse", tool_name="Agent", tool_use_id="call-a", tool_response={"status": "completed", "content": []})
        self.assertEqual(self.decision(prepared["decision_id"])["status"], "no_decision")
        with self.assertRaises(EvidenceError):
            self.authorize(prepared["decision_id"])

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
        self.assertEqual(self.decision(prepared["decision_id"])["status"], "no_decision")

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
        self.assertEqual({}, self.event("PreToolUse", tool_name="Agent", tool_use_id="resume-w", tool_input=resumed["input"]))
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
        raw = {"status": "completed", "agentId": "advisor-a", "resolvedModel": ROUTE["model"],
               "modelsUsed": [ROUTE["model"]], "totalTokens": 42,
               "content": [{"type": "text", "text": "RAW_BENCHMARK_SENTINEL"}]}
        event = self.event("PostToolUse", tool_name="Agent", tool_use_id="call-a", tool_response=raw)
        safe = event["hookSpecificOutput"]["updatedToolOutput"]
        self.assertEqual(set(raw), set(safe))
        self.assertEqual(safe["totalTokens"], 42)
        self.assertNotIn("RAW_BENCHMARK_SENTINEL", json.dumps(safe))
        self.assertEqual(self.decision(prepared["decision_id"])["advisor_provenance"]["observed_model"], ROUTE["model"])

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


if __name__ == "__main__":
    unittest.main()
