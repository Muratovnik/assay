"""Refused routing cannot establish a route; fixtures never launch a model."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/route-subagents/scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "hooks"))
from launch_preflight import RouteRefuted, check
from route_evidence.core import EvidenceError
from runtime import cli
import skill_reminder


def request(client="codex"):
    model = "worker" if client == "codex" else "sonnet"
    level_field = "reasoning_effort" if client == "codex" else "effort"
    top = "ultra" if client == "codex" else "max"
    return {"client": client, "mode": "evidence-only", "failure": "approval_rejected",
            "packet_id": "review", "available": [{"model": model, "efforts": ["medium", top]}],
            "selected": {"model": model, "effort": "medium"},
            "basis": {"source": "task", "reason": "Bounded review with frozen acceptance receipts and direct verification."},
            "launch": {"model": model, level_field: "medium", **({"fork_turns": "none"} if client == "codex" else {})},
            "tool_schema": {"properties": {"model": {}, level_field: {"enum": ["medium", top]},
                                           **({"fork_turns": {}} if client == "codex" else {})}},
            "spawn_fields": {"model": "model", "effort": level_field},
            **({"host": {"surface": "cli", "version": "2.1.295"}} if client == "claude" else {})}


def run_cli(data, env, cwd):
    payload = data if isinstance(data, str) else json.dumps(data)
    return subprocess.run([sys.executable, "-B", str(SCRIPTS / "launch_preflight.py"), "--request", "-"],
                          input=payload, capture_output=True, text=True, env=env, cwd=cwd)


class RefusalPreflightTests(unittest.TestCase):
    def test_explicit_supported_routes_preserve_input_and_unknown_runtime(self):
        for client in ("codex", "claude"):
            for failure in ("approval_rejected", "service_unavailable"):
                with self.subTest(client=client, failure=failure):
                    data = request(client); data["failure"] = failure
                    before = copy.deepcopy(data)
                    result = check(data, environment={})
                    self.assertEqual("arguments_checked", result["status"])
                    self.assertEqual(data["selected"], result["configured"])
                    self.assertEqual(before, data)
                    self.assertFalse(result["authorization_granted"])
                    self.assertFalse(result["launch_verified"])
                    self.assertIsNone(result["observed_effort"])

    def test_original_omitted_route_after_rejection_is_blocked_in_both_clients(self):
        for client in ("codex", "claude"):
            data = request(client)
            data["launch"] = {}
            data.pop("basis")
            with self.subTest(client=client), self.assertRaisesRegex(EvidenceError, "deliberate_selection_basis"):
                check(data, environment={})

    def test_incident_shape_with_a_stated_basis_is_refuted_by_the_parent_maximum(self):
        # The observed launch: a role, no route fields, the parent at maximum effort.
        incidents = (("codex", {"agent_type": "worker"}, {"model": "worker", "model_reasoning_effort": "ultra"}),
                     ("claude", {"subagent_type": "general-purpose"}, {"model": "sonnet", "effort": "max"}))
        for client, launch, parent in incidents:
            data = request(client)
            data["launch"] = launch
            data["parent"] = parent
            with self.subTest(client=client, role_declared=False), self.assertRaisesRegex(EvidenceError, "type_mismatch"):
                check(data, environment={})
            data["definition"] = {"name": next(iter(launch.values()))}
            with self.subTest(client=client), self.assertRaisesRegex(RouteRefuted, "effort_configuration_override"):
                check(data, environment={})
            data["inheritance_reason"] = "The parent route is reused."
            with self.subTest(client=client, reason=True), self.assertRaises(RouteRefuted):
                check(data, environment={})

    def test_parent_maximum_does_not_supply_missing_selection(self):
        for client in ("codex", "claude"):
            data = request(client)
            data.pop("selected")
            data["parent"] = {"model": "parent", "effort": "max", "model_reasoning_effort": "ultra"}
            with self.subTest(client=client), self.assertRaisesRegex(EvidenceError, "selected_model_and_effort"):
                check(data, environment={})

    def test_deliberate_maximum_user_choice_is_allowed(self):
        for client, level in (("codex", "ultra"), ("claude", "max")):
            data = request(client)
            data["selected"]["effort"] = level
            data["launch"][data["spawn_fields"]["effort"]] = level
            data["basis"] = {"source": "user", "reason": "The user explicitly selected this pair for this packet."}
            self.assertEqual(level, check(data, environment={})["configured"]["effort"])

    def test_full_history_rejects_overrides_and_unjustified_inheritance(self):
        data = request(); data["launch"]["fork_turns"] = "all"
        with self.assertRaisesRegex(EvidenceError, "full_history_cannot_express"):
            check(data)
        data["launch"] = {}
        data["parent"] = {"model": "worker", "model_reasoning_effort": "medium"}
        with self.assertRaisesRegex(EvidenceError, "inheritance_reason"):
            check(data)
        data["inheritance_reason"] = "Continuation needs the original history; confirmed parent pair is the selected pair."
        self.assertEqual(data["selected"], check(data)["configured"])
        data["parent"]["model_reasoning_effort"] = "ultra"
        with self.assertRaisesRegex(RouteRefuted, "conflicting"):
            check(data)

    def test_codex_recent_turn_count_accepts_explicit_route_only_when_exposed(self):
        for count in (3, "3"):
            data = request(); data["launch"]["fork_turns"] = count
            self.assertEqual(data["selected"], check(data)["configured"])
        data = request(); data["tool_schema"]["properties"].pop("fork_turns")
        with self.assertRaisesRegex(EvidenceError, "context_field_not_exposed"):
            check(data)
        for value in (0, -1, [], True, "last"):
            data = request(); data["launch"]["fork_turns"] = value
            with self.subTest(value=value), self.assertRaisesRegex(EvidenceError, "context_control_not_supported"):
                check(data)

    def test_codex_role_must_declare_its_definition(self):
        data = request(); data["launch"]["agent_type"] = "reviewer"
        with self.assertRaisesRegex(EvidenceError, "codex_definition_type_mismatch"):
            check(data)
        data["definition"] = {"name": "reviewer", "model": "worker", "model_reasoning_effort": "ultra"}
        with self.assertRaisesRegex(RouteRefuted, "effort_configuration_override"):
            check(data)
        data = request(); data["definition"] = {"name": "reviewer", "model_reasoning_effort": "medium"}
        with self.assertRaisesRegex(EvidenceError, "codex_definition_type_mismatch"):
            check(data)

    def test_codex_definition_can_express_pair_without_parent_inheritance(self):
        data = request(); data["launch"] = {"fork_turns": "none", "agent_type": "reader"}
        data["definition"] = {"name": "reader", "model": "worker", "model_reasoning_effort": "medium"}
        self.assertEqual(data["selected"], check(data)["configured"])

    def test_codex_rejects_arguments_its_schema_does_not_bind(self):
        for change in ({"effort": "medium"}, {"subagent_type": "reader"}, {"model_reasoning_effort": "medium"}):
            data = request(); data["launch"].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(EvidenceError, "argument_not_bound"):
                check(data)

    def test_absent_or_incomplete_schema_is_not_a_supported_route(self):
        for field in ("tool_schema", "spawn_fields"):
            data = request(); data.pop(field)
            with self.subTest(field=field), self.assertRaisesRegex(EvidenceError, "current_tool_schema"):
                check(data)
        data = request(); data["tool_schema"]["properties"].pop("reasoning_effort")
        with self.assertRaisesRegex(RouteRefuted, "spawn_field_not_exposed"):
            check(data)

    def test_required_routing_and_input_errors_cannot_be_replaced_by_this_check(self):
        for client in ("codex", "claude"):
            data = request(client); data["mode"] = "required"
            with self.subTest(client=client), self.assertRaisesRegex(EvidenceError, "registered_launch_not_local_fallback"):
                check(data, environment={})
        data = request(); data["failure"] = "invalid_advice"
        with self.assertRaisesRegex(EvidenceError, "invalid_failure"):
            check(data)
        data = request(); data["selected"]["effort"] = "unsupported"
        with self.assertRaisesRegex(EvidenceError, "not_in_current_inventory"):
            check(data)

    def test_claude_versioned_effort_and_definition_route(self):
        data = request("claude"); data["host"]["version"] = "2.1.291"
        with self.assertRaisesRegex(EvidenceError, "per_call_effort_not_supported"):
            check(data, environment={})
        data["launch"] = {"model": "sonnet", "subagent_type": "checked-reader"}
        data["definition"] = {"name": "checked-reader", "effort": "medium"}
        data["spawn_fields"]["effort"] = None
        self.assertEqual(data["selected"], check(data, environment={})["configured"])
        data["definition"]["name"] = "another-reader"
        with self.assertRaisesRegex(EvidenceError, "definition_type_mismatch"):
            check(data, environment={})

    def test_claude_definition_counts_only_when_the_call_selects_it(self):
        data = request("claude"); data["host"]["version"] = "2.1.291"
        data["spawn_fields"]["effort"] = None
        data["launch"] = {"model": "sonnet"}
        data["definition"] = {"effort": "medium"}
        with self.assertRaisesRegex(EvidenceError, "definition_type_mismatch"):
            check(data, environment={})
        data["launch"]["subagent_type"] = "checked-reader"
        data.pop("definition")
        with self.assertRaisesRegex(EvidenceError, "definition_type_mismatch"):
            check(data, environment={})

    def test_claude_unforced_environment_model_outranks_the_parent(self):
        data = request("claude"); data["launch"] = {"effort": "medium"}
        data["parent"] = {"model": "sonnet"}
        data["inheritance_reason"] = "The parent model is the selected model."
        with self.assertRaisesRegex(RouteRefuted, "model_configuration_override"):
            check(data, environment={"CLAUDE_CODE_SUBAGENT_MODEL": "opus"})
        data["parent"] = {"model": "opus"}
        data.pop("inheritance_reason")
        self.assertEqual("sonnet", check(data, environment={"CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"})["configured"]["model"])
        data["launch"]["subagent_type"] = "reader"
        data["definition"] = {"name": "reader", "model": "inherit"}
        with self.assertRaisesRegex(RouteRefuted, "model_configuration_override"):
            check(data, environment={"CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"})

    def test_claude_missing_effort_and_environment_override_block(self):
        data = request("claude"); data["launch"].pop("effort")
        data["parent"] = {"model": "opus", "effort": "max"}
        data["inheritance_reason"] = "History is needed."
        with self.assertRaisesRegex(RouteRefuted, "effort_configuration_override"):
            check(data, environment={})
        for environment, error in (({"CLAUDE_CODE_EFFORT_LEVEL": "max"}, RouteRefuted),
                                   ({"CLAUDE_CODE_EFFORT_LEVEL": "auto"}, EvidenceError),
                                   ({"CLAUDE_CODE_SUBAGENT_MODEL": "opus", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1"}, RouteRefuted)):
            with self.subTest(environment=environment), self.assertRaisesRegex(error, "fallback_route_"):
                check(request("claude"), environment=environment)
        with self.assertRaisesRegex(EvidenceError, "fallback_route_unresolved"):
            check(request("claude"), environment={"CLAUDE_CODE_EFFORT_LEVEL": "auto"})

    def test_claude_wrong_alias_fork_codex_controls_and_malformed_enum_block(self):
        for change, code in (({"model": "full-model-id"}, "native_alias"),
                             ({"subagent_type": "fork"}, "claude_fork_requires_parent_route"),
                             ({"reasoning_effort": "medium"}, "not_claude_controls")):
            data = request("claude"); data["launch"].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(EvidenceError, code):
                check(data, environment={})
        data = request("claude"); data["tool_schema"]["properties"]["effort"]["enum"] = "medium"
        with self.assertRaisesRegex(EvidenceError, "route_field_not_exposed"):
            check(data, environment={})

    def test_private_execution_prompt_is_not_a_preflight_input(self):
        data = request(); data["launch"]["message"] = "PRIVATE_SENTINEL"
        with self.assertRaisesRegex(EvidenceError, "routing_arguments_only"):
            check(data)

    def test_cli_is_local_and_separates_refuted_from_unverified(self):
        import os
        (ROOT / "tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp", prefix="refusal-") as temporary:
            cwd = Path(temporary)
            env = {**os.environ, "ASSAY_ROUTING_CONFIG": str(cwd / "missing.json"),
                   "ASSAY_ROUTING_CACHE_DIR": str(cwd / "cache")}
            for name in ("CLAUDE_CODE_EFFORT_LEVEL", "CLAUDE_CODE_SUBAGENT_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE"):
                env.pop(name, None)
            for client in ("codex", "claude"):
                data = request(client)
                result = run_cli(data, env, cwd)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertFalse(json.loads(result.stdout)["authorization_granted"])
                refuted = copy.deepcopy(data)
                refuted["launch"][data["spawn_fields"]["effort"]] = data["available"][0]["efforts"][1]
                result = run_cli(refuted, env, cwd)
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertEqual("refuted", json.loads(result.stdout)["outcome"])
                data["launch"] = {}; data.pop("basis")
                for payload in (data, "{not json", json.dumps({**request(client), "launch": {"fork_turns": []}})):
                    result = run_cli(payload, env, cwd)
                    self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                    self.assertEqual("unverified", json.loads(result.stdout)["outcome"])
            self.assertEqual([], list(cwd.iterdir()))


class RefusalDeliveryTests(unittest.TestCase):
    def test_refusal_procedure_is_delivered_before_every_launch_without_config(self):
        for client, tool in (("codex", "spawn_agent"), ("claude", "Agent")):
            with self.subTest(client=client):
                result, error = cli.process({"hook_event_name": "PreToolUse", "tool_name": tool}, client, {})
                self.assertIsNone(error)
                context = result["hookSpecificOutput"]["additionalContext"]
                self.assertIn("routing-failure.md", context)
                self.assertIn("rejected or unavailable", context)
                self.assertIn("do not launch", context)
                self.assertNotIn("permissionDecision", result["hookSpecificOutput"])

    def test_configured_routing_names_the_failure_branch_at_session_start(self):
        # The unconfigured session reminder stays within its budget and points
        # at route-subagents, which owns the failure branch.
        event = {"hook_event_name": "SessionStart", "source": "startup"}
        configured = skill_reminder.reminder(event, {"ASSAY_ROUTING_CONFIG": "routing.json"})
        self.assertIn("routing-failure.md", configured["hookSpecificOutput"]["additionalContext"])
        base = skill_reminder.reminder(event, {})["hookSpecificOutput"]["additionalContext"]
        self.assertIn("route-subagents before substantial solo work", base)


if __name__ == "__main__":
    unittest.main()
