"""Consumer regressions for cost units, quoted guidance and retained observations."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import time
import unittest

from test_task_evidence import CANDIDATES, PACKET, corpus, cost_chain, observation
from test_routing_history import decisions, snapshot
from route_evidence.core import EvidenceError, timestamp
from route_evidence.guides import GUIDES, guide_snapshot
from route_evidence.history import HistoryStore, import_history
from route_evidence.providers import SOURCES, captured_snapshot, parse_tables, snapshot as measured_snapshot
from route_evidence.routing import build_context
from route_evidence.task_costs import compare
from route_evidence.task_evidence import TaskEvidence, validate_summary


class MeasurementBoundaryTests(unittest.TestCase):
    def test_terminal_browser_keeps_run_totals_outside_comparable_expenses(self):
        proof = {"heading": "Terminal-Bench", "selected_version": "Terminal-Bench 4.0"}
        table = [["Model", "Agent", "Resolution Rate", "Tokens", "Cost"],
                 ["economy (low)", "Codex", "81% ± 5%", "1k", "$100"],
                 ["capable (high)", "Codex", "80% ± 5%", "2k", "$200"]]
        data = captured_snapshot(SOURCES["terminal-bench"], {"identity": proof, "parts": [
            {"subset": "all", "observed_subset": "all", "identity": proof, "tables": [table]}]})
        self.assertEqual(data["rows"][0]["aggregate_usage"], {"total_cost_usd": 100, "total_tokens": 1000})
        request = {"client": "codex", "task_types": ["terminal"], "max_cost_usd": 150,
                   "available": [{"model": c["model"], "efforts": [c["effort"]]} for c in CANDIDATES]}
        result = build_context(request, [{"source_id": "terminal-bench", "snapshot": data, "stale": False}])
        candidates = result["tasks"][0]["primary_comparisons"][0]["candidates"]
        for candidate in candidates:
            self.assertEqual(candidate["expenses"], {})
            self.assertEqual(candidate["dominated_by"], [])
            self.assertEqual(candidate["constraints"][0]["status"], "unknown")
        self.assertAlmostEqual(candidates[0]["score_low"], .76)
        self.assertAlmostEqual(candidates[0]["score_high"], .86)

    def test_published_overlap_is_not_lost_before_pareto_comparison(self):
        source = SOURCES["cursorbench"]
        table = [["Model", "Score", "Cost / Task", "Tokens / Task", "Steps / Task"],
                 ["economy (low)", "81% ± 5%", "$1", "100", "1"],
                 ["capable (high)", "80% ± 5%", "$2", "200", "2"]]
        data = measured_snapshot(source, parse_tables(source, [table]))
        request = {"client": "codex", "task_types": ["implementation"],
                   "available": [{"model": c["model"], "efforts": [c["effort"]]} for c in CANDIDATES]}
        result = build_context(request, [{"source_id": source["id"], "snapshot": data, "stale": False}])
        candidates = result["tasks"][0]["supporting_comparisons"][0]["candidates"]
        self.assertEqual([c["dominated_by"] for c in candidates], [[], []])
        self.assertEqual(candidates[0]["expenses"]["cost_usd"], 1)
        table[1][1] = "81% ± invalid"
        with self.assertRaises(EvidenceError):
            measured_snapshot(source, parse_tables(source, [table]))


class GuidanceBoundaryTests(unittest.TestCase):
    def guide(self, content):
        source = GUIDES["openai-reasoning"]
        first, second = source["sections"]
        return guide_snapshot(source, f"# Example\n\n## {first}\n\n{content}\n\n## {second}\n\nCosts.")

    def test_caveat_limits_fail_instead_of_publishing_incomplete_guidance(self):
        for content in ("\n\n".join(f"<Warning>condition {i}</Warning>" for i in range(7)),
                        "<Warning>" + "x" * 801 + " Do not use this setting.</Warning>"):
            with self.subTest(content=content[:60]), self.assertRaisesRegex(EvidenceError, "caveat"):
                self.guide(content)
        valid = self.guide("\n\n".join(f"<Warning>condition {i}</Warning>" for i in range(6)))
        self.assertEqual(len(valid["retrieved_sections"][0]["caveats"]), 6)

    def test_code_examples_do_not_become_vendor_caveats(self):
        for code in ("```xml\n<Warning>quoted example</Warning>\n```",
                     "````markdown\n```xml\n<Warning>quoted example</Warning>\n```\n````"):
            with self.subTest(code=code):
                section = self.guide(code + "\n\n<Note>Actual condition.</Note>")["retrieved_sections"][0]
                self.assertEqual(section["caveats"], [{"kind": "note", "text": "Actual condition.", "truncated": False}])
                self.assertEqual(section["code_blocks_omitted"], 1)


class LocalHistoryBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # The persistence format rounds to microseconds; that must not turn a
        # receipt made at this clock reading into future evidence.
        self.now = 1800000000.1234567
        self.history = HistoryStore(self.root, clock=lambda: self.now)
        self.evidence = TaskEvidence(self.root, {"enabled": True, "auto_download": False},
                                     history=self.history, clock=lambda: self.now)
        source = snapshot()
        source["evidence"]["task_similarity_evidence"] = {"schema_version": 1, "status": "available", "packets": []}
        self.packet = {k: source["packets"][0][k] for k in ("packet_id", "task_types", "features")}
        self.history.write_decision("observed", source, None, decisions())
        self.history.record_outcome("observed", {"status": "completed", "execution_ref": "run-1",
            "outcome": "accepted", "evidence_refs": ["acceptance-1"], "cost_observation": cost_chain()})

    def rows(self):
        return self.evidence.local_rows(self.packet, time.monotonic() + 5)

    def test_local_retrieval_reuses_history_identity_validation(self):
        self.assertEqual(len(self.rows()), 1)
        path = next(self.history.root.glob("outcome-*.json"))
        original = json.loads(path.read_text())
        for key, value in (("history_schema", 999), ("namespace", "foreign"), ("record_type", "decision"),
                           ("attempt_key", "0" * 64), ("decision_id", "other-decision")):
            path.write_text(json.dumps({**original, key: value}))
            with self.subTest(key=key), self.assertRaises(EvidenceError):
                self.rows()
        path.write_text(json.dumps(original))
        self.assertEqual(len(self.rows()), 1)

    def test_future_receipt_and_future_decision_cannot_train_current_estimates(self):
        self.now -= 86400
        with self.assertRaisesRegex(EvidenceError, "future"):
            self.rows()
        self.now += 86400
        path = self.history._path("observed", "decision")
        record = json.loads(path.read_text())
        record["created_at"] = timestamp(self.now + 86400)
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(EvidenceError, "future"):
            self.rows()

    def test_distinct_session_usage_is_not_deduplicated(self):
        events = [{"type": "event_msg", "timestamp": "2026-09-22T00:00:00Z", "payload": {
            "session_id": session, "info": {"last_token_usage": {"input_tokens": 10, "output_tokens": 5}}}}
            for session in ("session-a", "session-b")]
        path = self.root / "two-sessions.jsonl"
        path.write_text("".join(json.dumps(event) + "\n" for event in events))
        duplicate = self.root / "duplicate-prefix.jsonl"
        duplicate.write_text(json.dumps(events[0]) + "\n")
        result = import_history([path, duplicate])
        self.assertEqual(result["summary"]["request_events"], 2)
        self.assertEqual(result["summary"]["duplicates"], 1)
        self.assertEqual(result["summary"]["usage"]["total_tokens"], 30)

    def test_explicit_event_ids_are_scoped_to_session(self):
        for location in (("id",), ("uuid",), ("message", "id"),
                         ("payload", "id"), ("payload", "turn_id"), ("request_id",)):
            events = [{"type": "event_msg", "payload": {"session_id": session,
                "info": {"last_token_usage": {"input_tokens": 10, "output_tokens": 5}}}}
                for session in ("session-a", "session-b")]
            for event in events:
                target = event
                for key in location[:-1]:
                    target = target.setdefault(key, {})
                target[location[-1]] = "request-1"
            path = self.root / "explicit-ids.jsonl"
            path.write_text("".join(json.dumps(event) + "\n" for event in events))
            duplicate = self.root / "explicit-duplicate-prefix.jsonl"
            duplicate.write_text(json.dumps(events[0]) + "\n")
            result = import_history([path, duplicate])
            with self.subTest(location=location):
                self.assertEqual(result["summary"]["request_events"], 2)
                self.assertEqual(result["summary"]["duplicates"], 1)
                self.assertEqual(result["summary"]["usage"]["total_tokens"], 30)

    def test_codex_header_identity_scopes_events_without_repeated_ids(self):
        usage = {"type": "event_msg", "timestamp": "2026-10-09T00:00:01Z", "payload": {
            "type": "token_count", "info": {"last_token_usage": {"input_tokens": 10, "output_tokens": 5}}}}
        for fields in (("session_id",), ("id",), ("session_id", "id")):
            paths = []
            for name in ("a", "b"):
                meta = {field: f"{field}-{name}" for field in fields}
                events = [{"type": "session_meta", "payload": meta},
                          {"type": "turn_context", "payload": {"model": "same-model"}}, usage]
                path = self.root / f"header-{name}.jsonl"
                path.write_text("".join(json.dumps(event) + "\n" for event in events))
                paths.append(path)
            result = import_history([*paths, paths[0]])
            with self.subTest(fields=fields):
                self.assertEqual(result["summary"]["request_events"], 2)
                self.assertEqual(result["summary"]["duplicates"], 1)
                self.assertEqual(result["summary"]["usage"]["total_tokens"], 30)
                key = "session_id" if "session_id" in fields else "id"
                self.assertEqual({r["session_id"] for r in result["requests"]}, {f"{key}-a", f"{key}-b"})
                self.assertEqual([r["requested"]["model"] for r in result["requests"]], ["same-model", "same-model"])

    def test_codex_sibling_threads_keep_distinct_usage_and_context(self):
        events = []
        for name, total in (("a", 10), ("b", 10), ("a", 15)):
            events.extend([
                {"type": "session_meta", "payload": {"session_id": "root", "id": f"thread-{name}"}},
                {"type": "turn_context", "payload": {"model": f"model-{name}"}},
                {"id": f"event-{total}", "type": "event_msg", "payload": {
                    "info": {"total_token_usage": {"input_tokens": total, "output_tokens": 0}}}},
            ])
        path = self.root / "siblings.jsonl"
        path.write_text("".join(json.dumps(event) + "\n" for event in events))
        result = import_history([path, path])
        self.assertEqual(result["summary"]["request_events"], 3)
        self.assertEqual(result["summary"]["duplicates"], 3)
        self.assertEqual(result["summary"]["usage"]["input_tokens"], 25)
        self.assertEqual([r["thread_id"] for r in result["requests"]], ["thread-a", "thread-b", "thread-a"])
        self.assertEqual([r["requested"]["model"] for r in result["requests"]], ["model-a", "model-b", "model-a"])

    def test_codex_header_does_not_override_an_explicit_other_session(self):
        usage = {"type": "event_msg", "payload": {"session_id": "other", "info": {
            "last_token_usage": {"input_tokens": 10, "output_tokens": 5}}}}
        path = self.root / "explicit-other.jsonl"
        path.write_text("".join(json.dumps(event) + "\n" for event in [
            {"type": "session_meta", "payload": {"session_id": "root", "id": "root-thread"}},
            {"type": "turn_context", "payload": {"model": "root-model"}}, usage]))
        result = import_history([path])
        self.assertEqual(result["requests"][0]["session_id"], "other")
        self.assertIsNone(result["requests"][0].get("thread_id"))
        self.assertEqual(result["requests"][0]["requested"], {})

    def test_native_fork_owner_marker_preserves_prefix_dedup_and_cumulative_baseline(self):
        for child_session in ("parent-root", "new-root"):
            parent = {"type": "session_meta", "payload": {"session_id": "parent-root", "id": "parent"}}
            child = {"type": "session_meta", "payload": {
                "session_id": child_session, "id": "child", "forked_from_id": "parent"}}
            def total(ref, amount):
                return {"type": "event_msg", "id": ref, "payload": {"type": "token_count", "info": {
                    "total_token_usage": {"input_tokens": amount, "output_tokens": 0}}}}
            owner = {"type": "event_msg", "payload": {"type": "thread_settings_applied", "thread_id": "child"}}
            paths = []
            for name, events in (("parent", [parent, total("parent-call", 100)]),
                                 ("child", [child, parent, total("parent-call", 100), owner,
                                            total("child-call", 130), owner, total("child-next", 140)])):
                path = self.root / f"native-{name}.jsonl"
                path.write_text("".join(json.dumps(event) + "\n" for event in events))
                paths.append(path)
            for selected in (paths, paths[1:]):
                result = import_history(selected)
                with self.subTest(session=child_session, files=len(selected)):
                    self.assertEqual(result["status"], "complete")
                    self.assertEqual(result["summary"]["usage"]["input_tokens"], 140)
                    self.assertEqual(result["summary"]["request_events"], 3)
                    self.assertEqual(result["summary"]["duplicates"], len(selected) - 1)
                    self.assertEqual([r["thread_id"] for r in result["requests"]], ["parent", "child", "child"])
                    self.assertEqual([r["session_id"] for r in result["requests"]],
                                     ["parent-root", child_session, child_session])
                    self.assertEqual([r["usage"]["input_tokens"] for r in result["requests"]], [100, 30, 10])

    def test_referenced_history_without_a_local_counter_baseline_stays_unknown(self):
        meta = {"type": "session_meta", "payload": {"id": "child", "session_id": "root",
            "history_base": {"thread_id": "unnamed-ancestor", "end_ordinal_exclusive": 10, "end_byte_offset": 123}}}
        first = {"type": "event_msg", "payload": {"info": {
            "total_token_usage": {"input_tokens": 100, "output_tokens": 0}}}}
        second = {"type": "event_msg", "payload": {"info": {
            "total_token_usage": {"input_tokens": 130, "output_tokens": 0}}}}
        path = self.root / "referenced-history.jsonl"
        path.write_text("".join(json.dumps(event) + "\n" for event in (meta, first, second)))
        result = import_history([path])
        self.assertEqual(result["status"], "partial")
        self.assertIn("inherited_usage_baseline_unknown", [e["code"] for e in result["errors"]])
        self.assertIsNone(result["summary"]["usage"]["input_tokens"])
        self.assertEqual([r["usage"]["input_tokens"] for r in result["requests"]], [30])
        # Direct request usage is sufficient even when the cumulative prefix
        # lives in an explicitly unnamed ancestor file.
        first["payload"]["info"]["last_token_usage"] = {"input_tokens": 10, "output_tokens": 0}
        path.write_text("".join(json.dumps(event) + "\n" for event in (meta, first, second)))
        direct = import_history([path])
        self.assertEqual(direct["status"], "complete")
        self.assertEqual(direct["summary"]["usage"]["input_tokens"], 40)

    def test_nested_fork_requires_each_observed_owner_boundary(self):
        def meta(owner, parent=None):
            payload = {"id": owner, "session_id": "root"}
            if parent:
                payload["forked_from_id"] = parent
            return {"type": "session_meta", "payload": payload}
        def total(ref, amount, direct=None):
            info = {"total_token_usage": {"input_tokens": amount, "output_tokens": 0}}
            if direct is not None:
                info["last_token_usage"] = {"input_tokens": direct, "output_tokens": 0}
            return {"type": "event_msg", "id": ref, "payload": {"type": "token_count", "info": info}}
        for owner in ("parent", None, "omitted"):
            events = [meta("child", "parent"), meta("parent", "grandparent"), meta("grandparent"),
                      total("grand-call", 100)]
            if owner != "omitted":
                payload = {"type": "thread_settings_applied"}
                if owner:
                    payload["thread_id"] = owner
                events.append({"type": "event_msg", "payload": payload})
            events.extend([total("parent-call", 130),
                {"type": "event_msg", "payload": {"type": "thread_settings_applied", "thread_id": "child"}},
                total("child-call", 140, 10)])
            path = self.root / "nested-fork.jsonl"
            path.write_text("".join(json.dumps(event) + "\n" for event in events))
            result = import_history([path])
            with self.subTest(owner=owner):
                if owner == "parent":
                    self.assertEqual(result["status"], "complete")
                    self.assertEqual(result["summary"]["usage"]["input_tokens"], 140)
                    self.assertEqual([r["thread_id"] for r in result["requests"]], ["grandparent", "parent", "child"])
                else:
                    self.assertEqual(result["status"], "partial")
                    self.assertIn("inherited_owner_boundary_unknown", [e["code"] for e in result["errors"]])
                    self.assertIsNone(result["summary"]["usage"]["input_tokens"])
                    self.assertEqual(result["requests"], [])

    def test_unmarked_copied_fork_does_not_claim_complete_owner_or_total(self):
        events = [
            {"type": "session_meta", "payload": {"id": "child", "forked_from_id": "parent"}},
            {"type": "session_meta", "payload": {"id": "parent"}},
            {"type": "event_msg", "payload": {"info": {
                "total_token_usage": {"input_tokens": 100, "output_tokens": 0}}}},
            {"type": "event_msg", "payload": {"info": {
                "total_token_usage": {"input_tokens": 130, "output_tokens": 0}}}},
        ]
        path = self.root / "unmarked-fork.jsonl"
        path.write_text("".join(json.dumps(event) + "\n" for event in events))
        result = import_history([path])
        self.assertEqual(result["status"], "partial")
        self.assertIn("inherited_owner_boundary_unknown", [e["code"] for e in result["errors"]])
        self.assertIsNone(result["summary"]["usage"]["input_tokens"])
        self.assertEqual(result["summary"]["unattributed_usage_events"], 2)
        self.assertEqual(result["requests"], [])
        # A malformed ownership boundary cannot erase another client's known
        # observations in a combined export or poison the later parent's IDs.
        claude = {"type": "assistant", "sessionId": "claude-session", "uuid": "claude-call",
                  "message": {"usage": {"input_tokens": 7, "output_tokens": 3}}}
        path.write_text("".join(json.dumps(event) + "\n" for event in [*events, claude, claude]))
        parent = self.root / "independent-parent.jsonl"
        parent.write_text("".join(json.dumps(event) + "\n" for event in events[1:3]))
        mixed = import_history([path, parent])
        self.assertEqual([r["client"] for r in mixed["requests"]], ["claude", "codex"])
        self.assertEqual(mixed["summary"]["duplicates"], 1)
        self.assertEqual(mixed["requests"][1]["thread_id"], "parent")


class TaskChoiceBoundaryTests(unittest.TestCase):
    def test_model_only_choice_keeps_effort_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = TaskEvidence(Path(tmp), {"enabled": True, "auto_download": False})
            document = corpus()
            document["records"][0]["observations"] = [observation(), {**observation(), "effort": "high"}]
            evidence.install(document)
            candidates = [CANDIDATES[0], {**CANDIDATES[0], "candidate_id": "economy-high", "effort": "high"}]
            partial = {**PACKET, "explicit": {"model": "economy"}}
            result = evidence.summarize([partial], candidates, {"fix": "cache invalidation"})
            self.assertEqual(result["packets"][0]["neighbors"], 1)
            self.assertEqual(len(result["packets"][0]["public"]), 2)
            fixed = {**partial, "explicit": {"model": "economy", "effort": "low"}}
            self.assertEqual(evidence.summarize([fixed], candidates)["packets"][0]["status"], "skipped_fixed_route")

    def test_exact_paired_costs_do_not_depend_on_baseline_or_input_order(self):
        rows = [{"task_id": str(i), **observation(model, expense)} for i in range(3)
                for model, expense in (("economy", 2), ("capable", .4))]
        first = compare(rows, CANDIDATES, CANDIDATES[0]["candidate_id"], "api_usd", .05)
        second = compare(list(reversed(rows)), list(reversed(CANDIDATES)), CANDIDATES[1]["candidate_id"], "api_usd", .05)
        self.assertEqual(first["pairwise_comparisons"], second["pairwise_comparisons"])
        self.assertEqual(len(first["pairwise_comparisons"]), 1)
        pair = first["pairwise_comparisons"][0]
        costs = {c["candidate_id"]: 2 if c["model"] == "economy" else .4 for c in CANDIDATES}
        self.assertAlmostEqual(pair["cost_delta"], costs[pair["right_candidate_id"]] - costs[pair["left_candidate_id"]])
        self.assertEqual((pair["quality_delta"], pair["n"]), (0, 3))
        unknown_overhead = compare(rows, CANDIDATES, None, "api_usd", None)
        self.assertEqual(unknown_overhead["pairwise_comparisons"], first["pairwise_comparisons"])
        self.assertIsNone(unknown_overhead["net_benefit"])
        for changed in (rows + [copy.deepcopy(rows[0])],
                        [{**r, "cost_scope": "response"} for r in rows],
                        [{**r, "complete": False} for r in rows],
                        [{**r, "costs": {"api_usd": None}} for r in rows]):
            self.assertEqual(compare(changed, CANDIDATES, None, "api_usd", None)["pairwise_comparisons"], [])
        self.assertEqual(compare(rows, CANDIDATES, None, "api_usd", None, unit_basis="other-tariff")["pairwise_comparisons"], [])

    def test_pairwise_projection_rejects_invalid_numbers_and_duplicate_edges(self):
        rows = [{"task_id": str(i), **observation(model, expense)} for i in range(3)
                for model, expense in (("economy", 2), ("capable", .4))]
        comparison = compare(rows, CANDIDATES, None, "api_usd", None)
        summary = {"schema_version": 1, "status": "available", "packets": [{"packet_id": "fix", "comparison": comparison}]}
        validate_summary(summary)
        for field, value in (("cost_delta", float("inf")), ("quality_delta", .9), ("n", 0)):
            changed = copy.deepcopy(summary)
            changed["packets"][0]["comparison"]["pairwise_comparisons"][0][field] = value
            with self.subTest(field=field), self.assertRaises((EvidenceError, ValueError)):
                validate_summary(changed)
        changed = copy.deepcopy(summary)
        changed["packets"][0]["comparison"]["pairwise_comparisons"] *= 2
        with self.assertRaises(EvidenceError):
            validate_summary(changed)


if __name__ == "__main__":
    unittest.main()
