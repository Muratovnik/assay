"""Offline synthetic contracts for private routing history and log import."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "route-subagents" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from route_evidence.advice import build_snapshot, default_policy
from route_evidence.core import EvidenceError
from route_evidence.history import HistoryStore, import_history, replay


def snapshot(*, prompt=False):
    context = {
        "schema_version": 2, "client": "codex", "task_types": ["implementation"],
        "inventory": [{"model": "gpt-5.6-luna", "effort": "low"},
                      {"model": "gpt-6-astra", "effort": "medium"}],
        "tasks": [], "sources": [{"source_id": "bench-1"}], "excluded": [],
        "guidance": {}, "declared_constraints": {}, "warnings": [],
    }
    packets = [{
        "packet_id": "p1", "task_types": ["implementation"],
        "features": {"risk": {"value": "low", "provenance": "caller"}},
        "baseline": {"model": "gpt-6-astra", "effort": "medium"},
    }]
    value = build_snapshot(context, packets, policy=default_policy(),
                           created_at="2030-01-01T00:00:00Z",
                           expires_at="2030-01-01T01:00:00Z", client="codex")
    if prompt:
        value["task_prompt"] = "private task contents"
    return value


def advisor_result(value=None):
    value = value or snapshot()
    return {
        "schema_version": 1, "snapshot_id": value["snapshot_id"], "backend": "native-economy",
        "requested_model": "economy", "resolved_model": "gpt-5.6-luna", "effort": "low",
        "rankings": [{"packet_id": "p1", "ranking": list(value["packets"][0]["eligible"]), "ties": [],
                      "abstained": False, "reason_codes": ["advisor_ranked"],
                      "probabilities": None, "confidence": None}],
        "metadata": {"ignored": True},
    }


def decisions(selected=None):
    candidates = {item["candidate_id"]: item for item in snapshot()["candidates"]}
    selected = selected or next(key for key, value in candidates.items()
                                if value["model"] == "gpt-5.6-luna")
    return [{
        "packet_id": "p1", "status": "chosen", "decision_type": "advisor",
        "selected": candidates[selected], "reason_codes": ["advisor_ranked"],
        "ranking": [selected], "excluded": [], "fallback": None,
        "policy_hash": snapshot()["policy_hash"], "evidence_refs": ["bench-1"],
    }]


class HistoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.now = 1_800_000_000.0

    def store(self, **kwargs):
        return HistoryStore(self.root, clock=lambda: self.now, **kwargs)

    def test_off_metadata_and_full_have_distinct_privacy_boundaries(self):
        disabled_root = self.root / "disabled"
        disabled = HistoryStore(disabled_root, mode="off", clock=lambda: self.now)
        self.assertEqual(disabled.write_decision("d-off", snapshot(), advisor_result(), decisions()),
                         {"status": "disabled", "persisted": False})
        self.assertFalse((disabled_root / "routing-advisor").exists())

        metadata = self.store(mode="metadata")
        written = metadata.write_decision("d-meta", snapshot(), advisor_result(), decisions())
        self.assertEqual(written["write_status"], "written")
        self.assertNotIn("full", written)
        serialized = json.dumps(written)
        self.assertNotIn("task_types", serialized)
        self.assertNotIn("features", serialized)
        self.assertIn("gpt-5.6-luna", serialized)

        full = HistoryStore(self.root / "full-root", mode="full", clock=lambda: self.now)
        full_record = full.write_decision("d-full", snapshot(), advisor_result(), decisions())
        self.assertEqual(full_record["full"]["snapshot"]["packets"][0]["features"]["risk"],
                         {"value": "low", "provenance": "caller"})
        replayed = replay(full_record)
        self.assertEqual(replayed["decisions"][0]["decision_type"], "advisor")
        self.assertEqual(replayed["decisions"][0]["selected"]["model"], "gpt-5.6-luna")
        self.assertFalse(replayed["execution_authorized"])
        self.assertTrue(replayed["prediction_only"])
        self.assertEqual(replay(full_record, policy={"fallback": "none"})["status"],
                         "replayed")
        with self.assertRaises(EvidenceError):
            full.write_decision("d-private", snapshot(prompt=True), advisor_result(), decisions())

    def test_decisions_and_outcomes_are_immutable_and_observations_are_separate(self):
        store = self.store()
        first = store.write_decision("d1", snapshot(), advisor_result(), decisions())
        second = store.write_decision("d1", snapshot(), advisor_result(), decisions())
        self.assertEqual(first["write_status"], "written")
        self.assertEqual(second["write_status"], "unchanged")
        with self.assertRaisesRegex(EvidenceError, "conflicting"):
            other = next(item["candidate_id"] for item in snapshot()["candidates"]
                         if item["model"] == "gpt-6-astra")
            store.write_decision("d1", snapshot(), advisor_result(), decisions(other))

        outcome = store.record_outcome("d1", {
            "status": "completed", "execution_ref": "run-1",
            "requested": {"model": "gpt-5.6-luna", "effort": "low"},
            "actual_model": "gpt-6-astra", "actual_effort": "high",
            "usage": {"input_tokens": 20, "cached_input_tokens": 5,
                      "output_tokens": 8, "reasoning_output_tokens": 3},
            "usage_provenance": "observed:client_result", "outcome": "accepted",
        })
        execution = outcome["execution"]
        self.assertEqual(execution["requested"]["model"], "gpt-5.6-luna")
        self.assertEqual(execution["observed"]["model"], "gpt-6-astra")
        self.assertEqual(execution["outcome"]["status"], "unknown")
        self.assertIsNone(execution["usage"]["pricing_usd"])
        self.assertEqual(store.read("d1")["outcome_record"]["execution"], execution)

        with self.assertRaisesRegex(EvidenceError, "unknown decision"):
            store.record_outcome("missing", {"status": "unknown"})

    def test_accepted_outcome_requires_evidence_and_prune_ignores_foreign_files(self):
        store = self.store(retention_days=1)
        store.write_decision("d1", snapshot(), advisor_result(), decisions())
        accepted = store.record_outcome("d1", {
            "status": "completed", "outcome": {
                "status": "accepted", "basis": "user-confirmation",
                "evidence_refs": ["receipt-1"],
            },
        })
        self.assertEqual(accepted["execution"]["outcome"]["status"], "accepted")
        foreign = store.root / "foreign.json"
        foreign.write_text('{"expires_at":"2000-01-01T00:00:00Z"}', encoding="utf-8")
        self.now += 86401
        result = store.prune()
        self.assertEqual(result["deleted"], 2)
        self.assertTrue(foreign.exists())
        self.assertIsNone(store.read("d1"))

    def test_lifecycle_preserves_launch_and_one_terminal_receipt(self):
        store = self.store()
        store.write_decision("d-life", snapshot(), advisor_result(), decisions())
        launch = {"status": "launched", "execution_ref": "run-life",
                  "requested_model": "gpt-5.6-luna", "requested_effort": "low"}
        self.assertEqual(store.record_outcome("d-life", launch)["write_status"], "written")
        self.assertEqual(store.record_outcome("d-life", launch)["write_status"], "unchanged")
        completed = {"status": "completed", "execution_ref": "run-life",
                     "actual_model": "gpt-5.6-luna", "actual_effort": "low",
                     "outcome": {"status": "accepted", "basis": "test-receipt",
                                 "evidence_refs": ["receipt-life"]}}
        self.assertEqual(store.record_outcome("d-life", completed)["write_status"], "written")
        retained = store.read("d-life")["outcome_records"]
        self.assertEqual([item["execution"]["status"] for item in retained],
                         ["launched", "completed"])
        with self.assertRaisesRegex(EvidenceError, "terminal"):
            store.record_outcome("d-life", {"status": "failed",
                                             "execution_ref": "run-life"})

    def test_multi_packet_attempts_are_independent_and_explicit(self):
        store = self.store()
        multi_snapshot = snapshot()
        second_packet = json.loads(json.dumps(multi_snapshot["packets"][0]))
        second_packet["packet_id"] = "p2"
        multi_snapshot["packets"].append(second_packet)
        multi_snapshot["packet_ids"].append("p2")
        # Rebuild through the public constructor so hashes and eligibility remain valid.
        context = {
            "schema_version": 2, "client": "codex", "task_types": ["implementation"],
            "inventory": [{"model": item["model"], "effort": item["effort"]}
                          for item in multi_snapshot["candidates"]],
            "tasks": [], "sources": [], "excluded": [], "guidance": {},
            "declared_constraints": {}, "warnings": [],
        }
        packet = {key: multi_snapshot["packets"][0][key] for key in
                  ("packet_id", "task_types", "features", "explicit", "baseline",
                   "requirements", "capabilities")}
        packet2 = json.loads(json.dumps(packet)); packet2["packet_id"] = "p2"
        multi_snapshot = build_snapshot(context, [packet, packet2], policy=default_policy(),
                                        created_at="2030-01-01T00:00:00Z",
                                        expires_at="2030-01-01T01:00:00Z", client="codex")
        multi_decisions = decisions()
        multi_decisions.append({**multi_decisions[0], "packet_id": "p2"})
        store.write_decision("d-multi", multi_snapshot, None, multi_decisions)

        with self.assertRaisesRegex(EvidenceError, "packet_id is required"):
            store.record_outcome("d-multi", {"status": "completed"})
        for packet_id in ("p1", "p2"):
            receipt = store.record_outcome("d-multi", {
                "status": "completed", "packet_id": packet_id,
                "execution_ref": "run-" + packet_id,
            })
            self.assertEqual(receipt["packet_id"], packet_id)
        self.assertEqual(len(store.read("d-multi")["outcome_records"]), 2)
        with self.assertRaisesRegex(EvidenceError, "not part"):
            store.record_outcome("d-multi", {"status": "completed", "packet_id": "p3",
                                             "execution_ref": "run-p3"})
        with self.assertRaisesRegex(EvidenceError, "unsupported fields"):
            store.record_outcome("d-multi", {"status": "completed", "packet_id": "p1",
                                             "execution_ref": "retry", "api_key": "secret"})

    def test_root_refuses_symlink_ancestor_when_supported(self):
        target = self.root / "target"
        target.mkdir()
        link = self.root / "linked"
        try:
            os.symlink(target, link, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"host cannot create symlink: {exc}")
        with self.assertRaisesRegex(EvidenceError, "symlink or reparse"):
            HistoryStore(link)

    def test_full_history_accepts_validated_vendor_guidance_and_replays_policy(self):
        from route_evidence.routing import build_context
        from test_benchmark_router import guide_data, request, view

        guide = guide_data()
        guidance = [{
            "source_id": guide["guide_id"], "source_url": guide["canonical_url"],
            "snapshot": guide, "last_success_at": "2030-01-01T00:00:00Z",
            "stale": False,
        }]
        context = build_context(request(), [view()], guidance=guidance)
        packet = {
            "packet_id": "guided", "task_types": ["implementation"],
            "features": {"phase": {"value": "implementation", "provenance": "caller"}},
            "baseline": {"model": "frontier-a", "effort": "low"},
        }
        guided = build_snapshot(context, [packet], policy=default_policy(),
                                created_at="2030-01-01T00:00:00Z",
                                expires_at="2030-01-01T01:00:00Z", client="test-client")
        selected = next(item for item in guided["candidates"]
                        if item["model"] == "frontier-a" and item["effort"] == "low")
        decision = [{
            "packet_id": "guided", "status": "chosen", "decision_type": "fallback",
            "selected": selected, "reason_codes": ["caller_baseline"], "ranking": [],
            "excluded": guided["packets"][0]["excluded"],
            "fallback": {"status": "available", "selected": selected,
                         "reason": "caller_baseline"},
            "policy_hash": guided["policy_hash"],
            "evidence_refs": [guided["evidence_hash"]],
        }]
        store = HistoryStore(self.root / "guidance", mode="full", clock=lambda: self.now)
        stored = store.write_decision("d-guided", guided, None, decision)
        replayed = replay(store.read("d-guided"))
        self.assertEqual(stored["full"]["snapshot"]["evidence"]["guidance"]
                         ["documents"][0]["sections"][0]["excerpt"],
                         guide["retrieved_sections"][0]["excerpt"])
        self.assertEqual(replayed["status"], "replayed")
        self.assertFalse(replayed["execution_authorized"])


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, events):
        path = self.root / name
        path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        return path

    @staticmethod
    def cumulative(event_id, input_tokens, cached, output, reasoning, *, quota=False):
        info = {"total_token_usage": {
            "input_tokens": input_tokens, "cached_input_tokens": cached,
            "output_tokens": output, "reasoning_output_tokens": reasoning,
        }}
        if quota:
            info["rate_limits"] = {"primary": {"used_percent": 42.0}}
        return {"id": event_id, "type": "event_msg", "payload": {
            "session_id": "codex-session", "info": info,
        }}

    def test_cumulative_forks_resets_direct_usage_and_quota_are_counted_once(self):
        first = self.cumulative("e1", 100, 20, 30, 10, quota=True)
        second = self.cumulative("e2", 150, 30, 50, 20)
        direct = {"id": "e3", "type": "event_msg", "decision_id": "decision-3", "payload": {
            "session_id": "codex-session", "info": {
                "last_token_usage": {"input_tokens": 7, "cached_input_tokens": 2,
                                     "output_tokens": 4, "reasoning_output_tokens": 1},
                "total_token_usage": {"input_tokens": 157, "cached_input_tokens": 32,
                                      "output_tokens": 54, "reasoning_output_tokens": 21},
            }}}
        after_direct = self.cumulative("e5", 170, 35, 60, 24)
        reset = self.cumulative("e4", 20, 5, 8, 2)
        one = self.write("codex-one.jsonl", [first, second, direct, after_direct])
        fork = self.write("codex-fork.jsonl", [first, second, reset])

        report = import_history([one, fork])

        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["summary"]["duplicates"], 2)
        self.assertEqual(report["summary"]["request_events"], 5)
        self.assertEqual(report["summary"]["usage"]["input_tokens"], 190)
        self.assertEqual(report["summary"]["usage"]["output_tokens"], 68)
        self.assertEqual(report["summary"]["usage"]["cached_input_tokens"], 40)
        self.assertEqual(report["summary"]["usage"]["reasoning_output_tokens"], 26)
        linked = next(item for item in report["requests"]
                      if item["decision_link"] is not None)
        self.assertEqual(linked["decision_link"], {"decision_id": "decision-3",
                                                   "method": "explicit_id",
                                                   "confidence": "confirmed"})
        self.assertEqual(len(report["quota_timeline"]), 1)
        self.assertEqual(report["quota_timeline"][0]["scope"], "account")
        self.assertIsNone(report["quota_timeline"][0]["request_attribution"])

    def test_claude_direct_request_wins_over_result_aggregate(self):
        assistant = {
            "type": "assistant", "uuid": "assistant-event", "sessionId": "claude-session",
            "requested_model": "claude-sonnet", "requested_effort": "medium",
            "message": {"id": "msg-1", "model": "claude-opus", "usage": {
                "input_tokens": 10, "cache_read_input_tokens": 4,
                "cache_creation_input_tokens": 2, "output_tokens": 5,
                "service_tier": "standard",
            }},
        }
        duplicate_result = {
            "type": "result", "session_id": "claude-session", "model": "claude-opus",
            "usage": {"input_tokens": 16, "cache_read_input_tokens": 4,
                      "output_tokens": 5},
            "modelUsage": {"claude-opus": {"inputTokens": 16, "outputTokens": 5}},
        }
        direct_only_result = {
            "type": "result", "session_id": "result-only", "model": "claude-haiku",
            "effort": "low", "usage": {"input_tokens": 3, "output_tokens": 2,
                                          "service_tier": "priority"},
        }
        report = import_history([self.write("claude.jsonl", [assistant, duplicate_result,
                                                              direct_only_result])])

        self.assertEqual(report["summary"]["request_events"], 2)
        observed = report["requests"][0]
        self.assertEqual(observed["requested"]["model"], "claude-sonnet")
        self.assertEqual(observed["observed"]["model"], "claude-opus")
        self.assertNotIn("effort", observed["observed"])
        self.assertEqual(observed["observed"]["service_tier"], "standard")
        self.assertEqual(observed["usage"]["input_tokens"], 16)
        self.assertEqual(observed["usage"]["cached_input_tokens"], 4)
        self.assertIsNone(observed["usage"]["pricing_usd"])
        self.assertEqual(report["requests"][1]["observed"]["model"], "claude-haiku")
        self.assertEqual(report["requests"][1]["observed"]["effort"], "low")

    def test_malformed_and_missing_inputs_do_not_echo_raw_content_or_paths(self):
        bad = self.root / "secret-name.jsonl"
        bad.write_text('{"private":"DO-NOT-ECHO"\n', encoding="utf-8")
        missing = self.root / "also-secret.jsonl"
        report = import_history([bad, missing])
        rendered = json.dumps(report)
        self.assertEqual(report["status"], "partial")
        self.assertNotIn("DO-NOT-ECHO", rendered)
        self.assertNotIn("secret-name", rendered)
        self.assertEqual([error["source_index"] for error in report["errors"]], [0, 1])


class ReplayTests(unittest.TestCase):
    def test_metadata_is_explicitly_insufficient(self):
        record = {"history_schema": 1, "decision_id": "d1"}
        self.assertEqual(replay(record)["status"], "insufficient_record")

    def test_full_replay_forces_offline_policy_diagnostic(self):
        calls = {}
        fake = types.ModuleType("route_evidence.advice")

        def fake_default_policy(overrides=None):
            calls["overrides"] = overrides
            return default_policy(overrides)

        def decide(saved_snapshot, result=None, *, reason=None, offline=False):
            calls.update(snapshot=saved_snapshot, result=result, reason=reason, offline=offline)
            return [{"packet_id": "p1", "status": "chosen",
                     "decision_type": "advisor", "selected": {"candidate_id": "candidate"}}]

        fake.default_policy = fake_default_policy
        fake.decide = decide
        previous = sys.modules.get("route_evidence.advice")
        sys.modules["route_evidence.advice"] = fake
        self.addCleanup(lambda: (sys.modules.__setitem__("route_evidence.advice", previous)
                                 if previous is not None else
                                 sys.modules.pop("route_evidence.advice", None)))
        record = {"history_schema": 1, "decision_id": "d1", "full": {
            "snapshot": snapshot(), "advisor_result": advisor_result(),
        }}

        result = replay(record, policy={"fallback": "caller-baseline"})

        self.assertEqual(result["status"], "replayed")
        self.assertFalse(calls["offline"])
        self.assertEqual(calls["reason"], "history_replay")
        self.assertEqual(result["decisions"][0]["decision_type"], "advisor")
        self.assertFalse(result["execution_authorized"])
        self.assertIn("no_counterfactual_outcome", result["limitations"])

    def test_policy_change_that_changes_eligibility_is_insufficient(self):
        context = {
            "schema_version": 2, "client": "codex", "task_types": ["implementation"],
            "inventory": [{"model": "economy", "effort": "low"},
                          {"model": "frontier", "effort": "high"}],
            "tasks": [], "sources": [], "excluded": [], "guidance": {},
            "declared_constraints": {"max_cost_usd": 1}, "warnings": [],
        }
        packet = {"packet_id": "p1", "task_types": ["implementation"], "features": {}}
        value = build_snapshot(context, [packet], policy=default_policy(),
                               created_at="2030-01-01T00:00:00Z",
                               expires_at="2030-01-01T01:00:00Z", client="codex")
        result = {
            "schema_version": 1, "snapshot_id": value["snapshot_id"],
            "backend": "fixture", "requested_model": None, "resolved_model": None,
            "effort": None, "metadata": {},
            "rankings": [{"packet_id": "p1", "ranking": value["packets"][0]["eligible"],
                          "ties": [], "abstained": False, "reason_codes": [],
                          "probabilities": None, "confidence": None}],
        }
        record = {"history_schema": 1, "decision_id": "d-change", "full": {
            "snapshot": value, "advisor_result": result,
        }}
        replayed = replay(record, policy={"unknown_evidence": "strict"})
        self.assertEqual(replayed["status"], "insufficient_record")
        self.assertEqual(replayed["reason_codes"],
                         ["cannot_reuse_advisor_candidate_basis"])
        self.assertFalse(replayed["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
