"""Retrospective contracts: exact attribution, independent acceptance and privacy."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

from test_routing_history import snapshot, advisor_result, decisions

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
from route_evidence.core import EvidenceError
from route_evidence.history import HistoryStore
from route_evidence.telemetry import assess, observe_transcript, report
from runtime import routing_telemetry, cli

SPEC = {"goal": "Repair the parser", "criteria": [{"id": "roundtrip", "description": "Preserve round trips"},
        {"id": "reject", "description": "Reject malformed input"}], "verification": "Run parser acceptance checks",
        "error_impact": "medium", "ambiguity": "low", "provenance": "caller"}
IDENTITY = {"client": "claude", "session_id": "session-one", "agent_id": "worker-one"}


class RetrospectiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / "tmp")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.now = 1_800_000_000.0
        self.store = HistoryStore(self.root, retain_descriptions=True, dataset="production", clock=lambda: self.now)

    def decision(self, ident="d1", store=None, client="claude"):
        value = snapshot()
        value["client"] = client
        value["packets"][0]["task_spec"] = copy.deepcopy(SPEC)
        return (store or self.store).write_decision(ident, value, advisor_result(value), decisions())

    def terminal(self, ref="attempt-one", status="completed", runtime=IDENTITY, ident="d1"):
        return self.store.record_outcome(ident, {"packet_id": "p1", "execution_ref": ref, "status": status,
                                              "runtime": copy.deepcopy(runtime)})

    def assessment(self, ref="attempt-one", ident="a1", passed=True):
        return assess(self.store, {"decision_id": "d1", "packet_id": "p1", "execution_ref": ref,
            "assessment_id": ident, "source": "verification", "criteria": [
                {"id": "roundtrip", "status": "pass" if passed else "fail", "evidence_refs": ["roundtrip-check"]},
                {"id": "reject", "status": "pass", "evidence_refs": ["reject-check"]}]})

    def transcript(self, agent="worker-one", model="gpt-5.6-luna"):
        path = self.root / (agent + ".jsonl")
        path.write_text(json.dumps({"type": "assistant", "sessionId": "session-one", "agentId": agent,
            "uuid": "request-one", "message": {"model": model, "content": "PRIVATE_OUTPUT_SENTINEL",
                                                "usage": {"input_tokens": 10, "output_tokens": 4}}}) + "\n", encoding="utf-8")
        return path

    def observe(self, path, ref="attempt-one", runtime=IDENTITY):
        return observe_transcript(self.store, {"decision_id": "d1", "packet_id": "p1", "execution_ref": ref,
                                             "runtime": runtime, "transcript_path": str(path)})

    def test_task_context_is_retained_only_by_explicit_consent(self):
        self.decision()
        self.assertEqual(report(self.store)["packets"][0]["task"]["task_spec"], SPEC)
        private = HistoryStore(self.root / "no-consent", clock=lambda: self.now)
        self.decision(store=private)
        packet = report(private)["packets"][0]["task"]
        self.assertNotIn("task_spec", packet)
        self.assertEqual(packet["task_types"], ["implementation"])
        self.assertEqual(packet["features"]["risk"]["value"], "low")
        disabled = HistoryStore(self.root / "off", mode="off")
        self.assertEqual(report(disabled)["summary"]["packets"], 0)
        self.assertFalse(disabled.root.exists())

    def test_exact_native_import_retains_model_usage_but_no_path_or_output(self):
        self.decision(); self.terminal()
        path = self.transcript()
        self.observe(path); self.observe(path)
        result = report(self.store)
        self.assertEqual(result["summary"]["with_provider_model"], 1)
        attempt = result["packets"][0]["attempts"][0]
        self.assertEqual(attempt["provider_routes"], [{"model": "gpt-5.6-luna"}])
        self.assertEqual(attempt["usage"]["input_tokens"], 10)
        self.assertEqual(attempt["usage"]["output_tokens"], 4)
        self.assertEqual(attempt["usage_events"], 1)
        self.assertEqual(len(attempt["observations"]), 1)
        self.assertIsNone(attempt["whole_chain_cost"])
        text = json.dumps(result)
        self.assertNotIn("PRIVATE_OUTPUT_SENTINEL", text)
        self.assertNotIn(str(path), text)

    def test_other_worker_and_changed_attempt_identity_cannot_attach(self):
        self.decision(); self.terminal()
        with self.assertRaisesRegex(EvidenceError, "no attributable evidence"):
            self.observe(self.transcript(agent="worker-other"))
        with self.assertRaisesRegex(EvidenceError, "previously bound"):
            self.observe(self.transcript(), ref="attempt-other")
        self.store.record_outcome("d1", {"packet_id": "p1", "execution_ref": "retry", "status": "launched", "runtime": IDENTITY})
        with self.assertRaisesRegex(EvidenceError, "identity changed"):
            self.store.record_outcome("d1", {"packet_id": "p1", "execution_ref": "retry", "status": "completed",
                "runtime": {**IDENTITY, "agent_id": "other"}})

    def test_completion_and_unreferenced_pass_are_not_acceptance(self):
        self.decision(); self.terminal()
        self.assertIsNone(report(self.store)["summary"]["first_attempt_acceptance_rate"])
        assess(self.store, {"decision_id": "d1", "packet_id": "p1", "execution_ref": "attempt-one",
            "assessment_id": "unsubstantiated", "source": "user",
            "criteria": [{"id": "roundtrip", "status": "pass"}]})
        self.assertEqual(report(self.store)["summary"]["first_attempt_evaluated"], 0)

    def test_assessment_preserves_terminal_receipt_and_revisions(self):
        self.decision(); self.terminal()
        paths = list(self.store.root.glob("outcome-*.json"))
        original = paths[0].read_bytes()
        self.assessment(passed=False)
        self.now += 1
        self.assessment(ident="a2", passed=True)
        result = report(self.store)
        self.assertEqual(result["summary"]["first_attempt_acceptance_rate"], 1)
        self.assertEqual(len(result["packets"][0]["attempts"][0]["assessments"]), 2)
        self.assertEqual(paths[0].read_bytes(), original)
        with self.assertRaisesRegex(EvidenceError, "conflicting immutable"):
            self.assessment(ident="a2", passed=False)

    def test_retry_does_not_turn_first_attempt_failure_into_success(self):
        self.decision(); self.terminal()
        self.assessment(passed=False)
        self.now += 1
        self.terminal(ref="retry", runtime={**IDENTITY, "agent_id": "worker-two"})
        self.assessment(ref="retry", ident="retry-a", passed=True)
        summary = report(self.store)["summary"]
        self.assertEqual(summary["with_retries"], 1)
        self.assertEqual(summary["first_attempt_evaluated"], 1)
        self.assertEqual(summary["first_attempt_acceptance_rate"], 0)

    def test_unknown_criteria_and_unknown_attempt_are_rejected(self):
        self.decision(); self.terminal()
        with self.assertRaisesRegex(EvidenceError, "terminal attempt"):
            self.assessment(ref="missing")
        with self.assertRaisesRegex(EvidenceError, "unknown or duplicate"):
            assess(self.store, {"decision_id": "d1", "packet_id": "p1", "execution_ref": "attempt-one",
                "assessment_id": "bad", "source": "verification", "criteria": [{"id": "made-up", "status": "pass", "evidence_refs": ["test"]}]})

    def test_expired_history_and_smokes_do_not_pollute_production_report(self):
        self.decision()
        smoke = HistoryStore(self.root, clock=lambda: self.now, dataset="smoke", retain_descriptions=True)
        self.decision("smoke", smoke)
        result = report(self.store, dataset="production")
        self.assertEqual(result["summary"]["packets"], 1)
        self.assertEqual(result["summary"]["excluded_filter_decisions"], 1)
        self.now += 31 * 86400
        self.assertEqual(report(self.store)["summary"]["packets"], 0)

    def test_time_range_keeps_linked_attempts_and_legacy_retry_is_idempotent(self):
        from route_evidence.core import timestamp
        self.decision()
        self.terminal()
        path = next(self.store.root.glob("outcome-*.json"))
        old = json.loads(path.read_text(encoding="utf-8"))
        old.pop("dataset")
        path.write_text(json.dumps(old), encoding="utf-8")
        decision_path = next(self.store.root.glob("decision-*.json"))
        old_decision = json.loads(decision_path.read_text(encoding="utf-8"))
        old_decision.pop("dataset")
        decision_path.write_text(json.dumps(old_decision), encoding="utf-8")
        self.assertEqual(self.terminal()["write_status"], "unchanged")
        later = self.now + 3600
        self.now = later
        self.decision("later")
        result = report(self.store, since=timestamp(later))
        self.assertEqual([r["decision_id"] for r in result["packets"]], ["later"])
        older = report(self.store, until=timestamp(later))
        self.assertEqual(older["summary"]["with_attempts"], 1)
        with self.assertRaisesRegex(EvidenceError, "since must precede"):
            report(self.store, since=timestamp(later), until=timestamp(later))

    def test_codex_applied_settings_are_separate_from_provider_model(self):
        self.decision(client="codex")
        runtime = {"client": "codex", "session_id": "session-one", "thread_id": "child-thread"}
        self.terminal(runtime=runtime)
        path = self.root / "codex.jsonl"
        values = [
            {"type": "session_meta", "payload": {"id": "child-thread", "session_id": "session-one"}},
            {"type": "event_msg", "payload": {"type": "thread_settings_applied", "thread_id": "child-thread", "thread_settings": {"model": "gpt-6-astra", "reasoning_effort": "high"}}},
            {"type": "event_msg", "payload": {"type": "token_count", "info": {"last_token_usage": {"input_tokens": 12, "output_tokens": 3}}}},
        ]
        path.write_text("\n".join(json.dumps(v) for v in values) + "\n", encoding="utf-8")
        self.observe(path, runtime=runtime)
        summary = report(self.store)["summary"]
        self.assertEqual(summary["with_effective_settings"], 1)
        self.assertEqual(summary["effective_route_mismatches"], 1)
        self.assertEqual(summary["with_provider_model"], 0)
        self.assertEqual(summary["provider_mismatch_evaluable"], 0)

    def hook_binding(self):
        config = self.root / "config.json"
        config.write_text(json.dumps({"schema_version": 4, "client": "claude", "telemetry": {"mode": "metadata", "dataset": "production"},
                                      "task_evidence": {"retain_descriptions": True}}), encoding="utf-8")
        binding = self.root / "binding.json"
        binding.write_text(json.dumps({"config": str(config), "cache_dir": str(self.root)}), encoding="utf-8")
        return {"ASSAY_ROUTING_TELEMETRY_CONFIG": str(binding)}

    def test_native_stop_hook_captures_bound_worker_without_changing_payload(self):
        self.decision()
        self.store.record_outcome("d1", {"packet_id": "p1", "execution_ref": "attempt-one", "status": "launched", "runtime": IDENTITY})
        event = {"hook_event_name": "SubagentStop", "session_id": "session-one", "agent_id": "worker-one",
                 "agent_type": "custom-worker", "agent_transcript_path": str(self.transcript())}
        original = copy.deepcopy(event)
        result, error = cli.process(event, "claude", self.hook_binding(), clock=lambda: self.now)
        self.assertEqual(result, {})
        self.assertIsNone(error)
        self.assertEqual(event, original)
        self.assertEqual(report(self.store)["summary"]["with_provider_model"], 1)
        self.assertEqual(report(self.store)["summary"]["first_attempt_evaluated"], 0)

    def test_hook_is_opt_in_and_does_not_read_unbound_transcript(self):
        self.decision()
        event = {"hook_event_name": "SubagentStop", "session_id": "session-one", "agent_id": "unbound",
                 "agent_transcript_path": str(self.root / "missing.jsonl")}
        routing_telemetry.capture(event, "claude", {}, clock=lambda: self.now)
        routing_telemetry.capture(event, "claude", self.hook_binding(), clock=lambda: self.now)
        self.assertEqual(report(self.store)["summary"]["with_attempts"], 0)

    def test_native_launch_link_collects_without_manual_receipt(self):
        self.decision()
        env = self.hook_binding()
        launch = {"session_id": "session-one", "tool_use_id": "native-tool-one", "tool_name": "Agent",
                  "tool_input": {"prompt": "PRIVATE_LAUNCH_SENTINEL\n[assay-routing:d1/p1]"}}
        routing_telemetry.capture({**launch, "hook_event_name": "PreToolUse"}, "claude", env, clock=lambda: self.now)
        routing_telemetry.capture({**launch, "hook_event_name": "PostToolUse", "tool_response": {"agentId": "worker-one"}}, "claude", env, clock=lambda: self.now)
        routing_telemetry.capture({"session_id": "session-one", "agent_id": "worker-one", "hook_event_name": "SubagentStop",
            "agent_transcript_path": str(self.transcript())}, "claude", env, clock=lambda: self.now)
        result = report(self.store)
        self.assertEqual(result["summary"]["with_attempts"], 1)
        self.assertEqual(result["summary"]["with_provider_model"], 1)
        attempt = result["packets"][0]["attempts"][0]
        self.assertEqual(attempt["receipts"], [])
        self.assertNotIn("PRIVATE_LAUNCH_SENTINEL", json.dumps(result))
        self.assertEqual(result["summary"]["first_attempt_evaluated"], 0)

    def test_native_failed_launch_is_an_attempt_without_invented_worker(self):
        self.decision()
        env = self.hook_binding()
        launch = {"session_id": "session-one", "tool_use_id": "native-tool-one", "tool_name": "Agent",
                  "tool_input": {"prompt": "[assay-routing:d1/p1]"}}
        routing_telemetry.capture({**launch, "hook_event_name": "PreToolUse"}, "claude", env, clock=lambda: self.now)
        routing_telemetry.capture({**launch, "hook_event_name": "PostToolUseFailure"}, "claude", env, clock=lambda: self.now)
        result = report(self.store)
        self.assertEqual(result["summary"]["with_attempts"], 1)
        self.assertEqual(result["summary"]["with_provider_model"], 0)
        self.assertEqual(result["packets"][0]["attempts"][0]["observations"][0]["status"], "failed")

    def test_native_completed_return_keeps_duration_and_aggregate_usage_separate(self):
        from claude_output_fixture import completed_output
        self.decision()
        env = self.hook_binding()
        launch = {"session_id": "session-one", "tool_use_id": "native-tool-one", "tool_name": "Agent",
                  "tool_input": {"prompt": "[assay-routing:d1/p1]"}}
        routing_telemetry.capture({**launch, "hook_event_name": "PreToolUse"}, "claude", env, clock=lambda: self.now)
        routing_telemetry.capture({**launch, "hook_event_name": "PostToolUse", "tool_response": completed_output(agentId="worker-one")},
                                  "claude", env, clock=lambda: self.now)
        result = report(self.store)
        attempt = result["packets"][0]["attempts"][0]
        self.assertEqual(attempt["duration_seconds"], .125)
        self.assertEqual(attempt["worker_return_usage"]["input_tokens"], 30)
        self.assertEqual(attempt["usage_events"], 0)
        self.assertEqual(result["summary"]["with_provider_model"], 0)
        self.assertNotIn("PRIVATE_REPORT", json.dumps(result))

    def test_foreground_stop_before_return_is_attributed_after_exact_worker_id(self):
        self.decision()
        env = self.hook_binding()
        launch = {"session_id": "session-one", "tool_use_id": "native-tool-one", "tool_name": "Agent",
                  "tool_input": {"prompt": "[assay-routing:d1/p1]"}}
        routing_telemetry.capture({**launch, "hook_event_name": "PreToolUse"}, "claude", env, clock=lambda: self.now)
        routing_telemetry.capture({"session_id": "session-one", "agent_id": "worker-one", "hook_event_name": "SubagentStop",
            "agent_transcript_path": str(self.transcript())}, "claude", env, clock=lambda: self.now)
        self.assertEqual(report(self.store)["summary"]["with_attempts"], 0)
        routing_telemetry.capture({**launch, "hook_event_name": "PostToolUse", "tool_response": {"agentId": "worker-one"}}, "claude", env, clock=lambda: self.now)
        result = report(self.store)
        self.assertEqual(result["summary"]["with_attempts"], 1)
        self.assertEqual(result["summary"]["with_provider_model"], 1)
        from route_evidence.pipeline_store import PipelineStore
        with PipelineStore(self.root / "routing-telemetry-hooks", clock=lambda: self.now).transaction() as tx:
            self.assertEqual(tx.values("pending-stop"), [])

    def test_parallel_launches_use_exact_returned_identity(self):
        self.decision(); self.decision("d2")
        env = self.hook_binding()
        for did, tool in (("d1", "first-tool"), ("d2", "second-tool")):
            routing_telemetry.capture({"session_id": "session-one", "tool_use_id": tool, "tool_name": "Agent",
                "hook_event_name": "PreToolUse", "tool_input": {"prompt": f"[assay-routing:{did}/p1]"}},
                "claude", env, clock=lambda: self.now)
        for worker in ("worker-one", "worker-two"):
            routing_telemetry.capture({"session_id": "session-one", "agent_id": worker,
                "hook_event_name": "SubagentStop", "agent_transcript_path": str(self.transcript(worker))},
                "claude", env, clock=lambda: self.now)
        for tool, worker in (("second-tool", "worker-two"), ("first-tool", "worker-one")):
            routing_telemetry.capture({"session_id": "session-one", "tool_use_id": tool, "tool_name": "Agent",
                "hook_event_name": "PostToolUse", "tool_response": {"agentId": worker}},
                "claude", env, clock=lambda: self.now)
        result = report(self.store)
        self.assertEqual(result["summary"]["with_provider_model"], 2)
        for row in result["packets"]:
            expected = "worker-one" if row["decision_id"] == "d1" else "worker-two"
            imported = next(o for o in row["attempts"][0]["observations"] if "requests" in o)
            self.assertEqual(imported["runtime"]["agent_id"], expected)

    def test_telemetry_failure_preserves_hook_permission_reply(self):
        from unittest.mock import patch
        event = {"hook_event_name": "PreToolUse", "session_id": "session-one", "tool_name": "Agent", "tool_input": {}}
        reply = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}
        with patch.object(cli, "_process", return_value=(reply, None)), patch.object(routing_telemetry, "capture", side_effect=EvidenceError("private detail")):
            result, error = cli.process(event, "claude", {})
        self.assertEqual(result, reply)
        self.assertIn("telemetry unavailable", error)
        self.assertNotIn("private detail", error)
        denied = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny"}}
        with patch.object(cli, "_process", return_value=(denied, None)), patch.object(routing_telemetry, "capture") as capture:
            self.assertEqual(cli.process(event, "claude", {}), (denied, None))
            capture.assert_not_called()

    def test_full_context_opt_out_purges_task_spec_and_diagnostic_snapshot(self):
        from route_evidence.advice import build_snapshot, default_policy
        from route_evidence.task_evidence import TaskEvidence
        context = {"schema_version": 2, "client": "claude", "task_types": ["implementation"],
            "inventory": [{"model": "gpt-5.6-luna", "effort": "low"}], "tasks": [], "sources": [],
            "excluded": [], "guidance": {}, "declared_constraints": {}, "warnings": []}
        packet = {"packet_id": "p1", "task_types": ["implementation"], "features": {}, "task_spec": SPEC}
        value = build_snapshot(context, [packet], policy=default_policy(), created_at="2030-01-01T00:00:00Z",
                               expires_at="2030-01-01T01:00:00Z", client="claude")
        full = HistoryStore(self.root / "full", mode="full", retain_descriptions=True, clock=lambda: self.now)
        full.write_decision("full-context", value, None, decisions())
        self.assertIn("full", full.read("full-context"))
        self.assertEqual(TaskEvidence(self.root, history=full).purge_descriptions()["records"], 1)
        stored = full.read("full-context")
        self.assertNotIn("full", stored)
        self.assertNotIn("Repair the parser", json.dumps(stored))


if __name__ == "__main__":
    unittest.main()
