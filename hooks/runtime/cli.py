#!/usr/bin/env python3
"""One plugin entry per event; only the routing owner can reject an operation."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
# -I ignores cwd/PYTHONPATH. Import only installed, task-owned modules.
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime.activation import evaluate, load_rules
from runtime.events import normalize
from runtime import state, feedback, routing_telemetry, skill_gate
from route_evidence.client_capabilities import contract, codex_route_check
from route_evidence.core import loads
from route_evidence import route_table
from route_evidence.service import load_config
from routing_hook import handle as route, explicit_launch, failure, deny, routing_operation
from skill_reminder import reminder

MAX_INPUT = 1024 * 1024


def read_json(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        raise ValueError("oversized configuration")
    value = loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("configuration must be an object")
    return value


def options(environment):
    location = environment.get("ASSAY_HOOK_CONFIG")
    if location and (not isinstance(location, str) or not Path(location).is_absolute()):
        raise ValueError("hook configuration path must be absolute")
    raw = read_json(location) if location else {}
    if set(raw) - {"disabled_rules", "disabled_skills", "state_dir", "record_events",
                   "feedback_capture", "feedback_trigger"}:
        raise ValueError("unknown hook option")
    # Storage defaults to metadata for explicit records; the correction
    # grammar stays off until the owner selects the hook trigger.
    value = {"disabled_rules": [], "disabled_skills": [], "record_events": False,
             "feedback_capture": "metadata", "feedback_trigger": "explicit",
             "state_dir": environment.get("PLUGIN_DATA") or environment.get("CLAUDE_PLUGIN_DATA"), **raw}
    for key in ("disabled_rules", "disabled_skills"):
        if not isinstance(value[key], list) or any(not isinstance(v, str) for v in value[key]):
            raise ValueError("invalid disabled rules or skills")
    if type(value["record_events"]) is not bool:
        raise ValueError("invalid recording option")
    if not isinstance(value["feedback_capture"], str) or value["feedback_capture"] not in feedback.MODES:
        raise ValueError("invalid feedback capture mode")
    if not isinstance(value["feedback_trigger"], str) or value["feedback_trigger"] not in feedback.TRIGGERS:
        raise ValueError("invalid feedback trigger")
    if value["state_dir"] is not None and (not isinstance(value["state_dir"], str) or not Path(value["state_dir"]).is_absolute()):
        raise ValueError("hook state directory must be absolute")
    return value


def explicit_routes(event, client, environment, config=None):
    """Evidence-only launch check; the configuration may come from the telemetry binding.

    That binding names the routing configuration whose launches it records, so
    an owner who set up evidence-only routing gets the check without another
    setting. With a route table every spawn must follow its declared class,
    and a spawn the table does not check is pointed at it instead of the
    generic launch reminder; without one a Claude spawn must still name both
    settings. A missing or unreadable configuration keeps ordinary delegation.
    """
    spec = route_table.SPAWN.get(client)
    if (spec is None or event.get("hook_event_name") != "PreToolUse"
            or event.get("tool_name") not in spec["tools"]):
        return {}
    try:
        if config is None:
            binding = routing_telemetry.configuration(environment)
            if binding is None:
                return {}
            config = load_config(Path(binding["config"]))
        table = config.get("routes")
        if table is None:
            return explicit_launch(event, config) if client == "claude" else {}
        mode = config["pipeline"]
        if config.get("client") != client or mode["mode"] != "evidence-only":
            return {}
        # The table, not the generic launch reminder, describes routing here.
        outside = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": route_table.OUTSIDE}}
        if mode["explicit_routes"] != "require":
            return outside
        reason = route_table.check_launch(client, event.get("tool_name"), event.get("tool_input"), table,
                                          unrouted=mode["unrouted_agents"], environment=environment,
                                          cwd=event.get("cwd"))
        if reason:
            return deny(reason)
        note = route_table.admission(client, event.get("tool_name"), event.get("tool_input"), table,
                                     unrouted=mode["unrouted_agents"])
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": note}} if note else outside
    except Exception:
        return {}


def routing_result(event, client, environment):
    path = environment.get("ASSAY_ROUTING_CONFIG")
    if not path:
        return explicit_routes(event, client, environment)
    try:
        config = load_config(Path(path))
        if config.get("pipeline", {}).get("mode") != "required":
            return explicit_routes(event, client, environment, config)
        if client != "claude" or config.get("client") != client:
            if event.get("hook_event_name") == "PreToolUse" and (
                    event.get("tool_name") in {"spawn_agent", "Agent", "Task"}
                    or routing_operation(event.get("tool_name")) is not None):
                return deny("required routing is unavailable for this client contract; use evidence-only mode explicitly, not an implicit bypass")
            if event.get("hook_event_name") == "SessionStart":
                return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext":
                    "Assay: required routing is not supported by this configured client adapter. Protected delegation is blocked; ordinary root work remains available. Run the routing doctor."}}
            return {}
        if event.get("hook_event_name") == "UserPromptSubmit":
            return {}
        return route(event, config, environment=environment)
    except Exception:
        # Do not let an advisory dependency or malformed config downgrade an
        # explicitly selected contract. Echo neither paths nor payloads.
        if client == "codex" and event.get("hook_event_name") == "PreToolUse" and event.get("tool_name") == "spawn_agent":
            return deny("required routing configuration could not be validated")
        return failure(event, "plugin", True)


READ_TOOLS = frozenset({"Read", "Grep", "Glob", "read_file", "list_dir", "find_file", "view_image",
                        "search_for_pattern", "get_symbols_overview", "find_symbol", "find_referencing_symbols",
                        "read_mcp_resource", "list_mcp_resources", "list_mcp_resource_templates",
                        "search_openai_docs", "fetch_openai_doc"})
# The host channel that delivers a subagent's final report to the primary. A
# reading role exists to return findings; denying it silences the review.
REPORT_TOOLS = frozenset({"SubagentHandback"})
# Tools a profile's own projection grants beyond workspace reading.
PROFILE_TOOLS = {"official-docs-researcher": frozenset({"WebFetch", "WebSearch", "ToolSearch"})}


def reading_profile(role):
    """The reading profile a native agent type names, or None."""
    import re
    if not isinstance(role, str):
        return None
    name = role.split(":")[-1]
    if name in {"evidence-reviewer", "official-docs-researcher"}:
        return name
    match = re.fullmatch(
        r"assay-(evidence-reviewer|official-docs-researcher)-(?:low|medium|high|xhigh|max|ultra)-[0-9a-f]{16}", name)
    return match[1] if match else None


def reading_role(role):
    return reading_profile(role) is not None


def reviewer_boundary(event, environment, *, clock=None):
    role = event.get("agent_type")
    reading = reading_role(role)
    if isinstance(role, str) and not reading:
        return {}
    if event.get("hook_event_name") not in {"SubagentStart", "PreToolUse"}:
        return {}
    session, agent = event.get("session_id"), event.get("agent_id")
    directory = environment.get("PLUGIN_DATA") or environment.get("CLAUDE_PLUGIN_DATA")
    if directory and isinstance(session, str) and session and (not reading or event["hook_event_name"] == "SubagentStart"):
        from route_evidence.core import digest
        from route_evidence.pipeline_store import PipelineStore
        import re
        import time
        now = clock() if clock else time.time()
        observed_agent = agent
        if not observed_agent and isinstance(event.get("transcript_path"), str):
            match = re.search(r"([0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})\.jsonl$", event["transcript_path"])
            observed_agent = match[1] if match else None
        if isinstance(observed_agent, str) and observed_agent:
            key = digest({"session": session, "agent": observed_agent})
            boundary_root = Path(directory) / "profile-boundaries"
            if event["hook_event_name"] == "PreToolUse" and not boundary_root.exists():
                return {}
            with PipelineStore(boundary_root, clock=clock or time.time).transaction() as tx:
                if event.get("hook_event_name") == "SubagentStart" and isinstance(role, str):
                    tx.put("profile", key, {"role": role}, now + 86400)
                elif not role:
                    record = tx.get("profile", key)
                    role = record["role"] if record else None
    profile = reading_profile(role)
    if event.get("hook_event_name") != "PreToolUse" or profile is None:
        return {}
    tool = event.get("tool_name", "")
    if (tool in READ_TOOLS | REPORT_TOOLS | PROFILE_TOOLS.get(profile, frozenset())
            or (tool.startswith(("mcp__serena__", "mcp__openaiDeveloperDocs__"))
                and tool.rsplit("__", 1)[-1] in READ_TOOLS)):
        return {}
    return deny("This profile is a reading role: return findings and receipts to the primary; "
                "task/checklist, memory, file writes, shell execution and further delegation are unavailable")


def _process(event, client, environment, *, root=ROOT, clock=None):
    normalized = normalize(event, client)
    if normalized is None:
        return {}, None
    try:
        protected = reviewer_boundary(event, environment, clock=clock) or routing_result(event, client, environment)
    except Exception:
        if event.get("hook_event_name") == "PreToolUse":
            return deny("read-only profile identity could not be checked; repair the profile hook state before retrying"), None
        return {}, "Assay: profile identity capture unavailable; reviewer enforcement is unverified."
    denied = protected.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
    outcome = "deny" if denied else "guard" if protected else None
    legacy = {}
    try:
        # Basic reminders do not depend on prompt rules, the parser or state.
        # Keep them as a fallback; a routing reply always remains authoritative.
        if not protected and event["hook_event_name"] in {"SessionStart", "PreToolUse"}:
            legacy = reminder(event, environment)
        settings = options(environment)
        rules, fingerprint = load_rules(root, disabled_rules=settings["disabled_rules"], disabled_skills=settings["disabled_skills"])
        if client == "claude" and rules.skill_gate and settings["state_dir"]:
            # Records skill loads on PreToolUse; on Stop it can hold a reply to
            # the skills it named. A guard reply keeps priority.
            names = {rule["skill"].split("/", 1)[1] for rule in rules}
            gate = skill_gate.apply(event, client, names, settings["state_dir"],
                                    **({"clock": clock} if clock else {}))
            if gate and not protected:
                return gate, None
        decision = {"rule_ids": [], "context": ""} if protected else evaluate(event, rules)
        if legacy:
            decision["context"] = legacy["hookSpecificOutput"]["additionalContext"]
        if settings["state_dir"]:
            kwargs = {"clock": clock} if clock else {}
            decision = state.apply(event, client, decision, rules, fingerprint, settings["state_dir"],
                                   record=settings["record_events"], outcome=outcome, **kwargs)
        if protected:
            return protected, None  # One voice; no competing permission/argument writers.
        if decision["context"]:
            return {"hookSpecificOutput": {"hookEventName": event["hook_event_name"],
                                          "additionalContext": decision["context"]}}, None
        return {}, None
    except Exception:
        return protected or legacy, "Assay: optional hints unavailable; routing decision and basic reminders retained. Run hooks doctor."


def process(event, client, environment, *, root=ROOT, clock=None):
    result, error = _process(event, client, environment, root=root, clock=clock)
    try:
        if result.get("hookSpecificOutput", {}).get("permissionDecision") != "deny":
            routing_telemetry.capture(event, client, environment, **({"clock": clock} if clock else {}))
    except Exception:
        diagnostic = "Assay: routing execution telemetry unavailable; hook decision retained. Check telemetry binding and native identity."
        error = "\n".join(part for part in (error, diagnostic) if part)
    if event.get("hook_event_name") != "UserPromptSubmit":
        return result, error
    # Feedback may append context, never merge into a permission decision or
    # replacement payload. Failure in this optional feature preserves the first
    # owner's complete result. No second native handler is registered.
    if result and (set(result) != {"hookSpecificOutput"} or
                   set(result["hookSpecificOutput"]) - {"hookEventName", "additionalContext"}):
        return result, error
    try:
        kwargs = {"clock": clock} if clock else {}
        extra = feedback.handle(event, client, options(environment), root=root, **kwargs)
        if extra:
            original = result.get("hookSpecificOutput", {}).get("additionalContext", "")
            message = extra["hookSpecificOutput"]["additionalContext"]
            result = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                      "additionalContext": "\n".join(part for part in (original, message) if part)}}
    except Exception:
        diagnostic = "Assay: optional feedback capture unavailable; existing hook result retained. Check feedback configuration, capacity and permissions."
        error = "\n".join(part for part in (error, diagnostic) if part)
    return result, error


def record_command(environment, settings, root):
    """Name the explicit record command, since a model shell may not see plugin variables."""
    if settings["feedback_capture"] == "off":
        return {"available": False, "reason": "feedback_capture is off"}
    if not settings["state_dir"]:
        return {"available": False, "reason": "no state directory configured"}
    location = environment.get("ASSAY_HOOK_CONFIG")
    return {"available": True,
            "argv": ["python", "-I", "-B", str(root / "hooks/runtime/feedback_cli.py"), "record",
                     *(["--config", location] if location else []),
                     "--state-dir", settings["state_dir"], "--input", "CASE.json"]}


def doctor(client, environment, *, root=ROOT, settings_path=None):
    settings = options(environment)
    rules, fingerprint = load_rules(root, disabled_rules=settings["disabled_rules"], disabled_skills=settings["disabled_skills"])
    config = load_config(Path(environment["ASSAY_ROUTING_CONFIG"])) if environment.get("ASSAY_ROUTING_CONFIG") else {}
    result = {"capabilities": contract(client, config.get("pipeline", {}).get("host")),
              "rules": [r["id"] for r in rules], "rules_fingerprint": fingerprint,
              "skill_check": rules.skill_check,
              "prompt_parser_available": importlib.util.find_spec("markdown_it") is not None,
              "state_configured": settings["state_dir"] is not None,
              "record_events": settings["record_events"], "hooks_trusted": "unknown",
              "feedback_capture": settings["feedback_capture"],
              "feedback_trigger": settings["feedback_trigger"],
              "feedback_record": record_command(environment, settings, root),
              "native_execution": "unverified", "model_compliance": "unverified",
              "routing_telemetry_bound": routing_telemetry.configuration(environment) is not None,
              "settings_modified": False, "conflicts": []}
    if settings_path:
        supplied = read_json(settings_path).get("hooks", {})
        if not isinstance(supplied, dict):
            raise ValueError("invalid client hooks")
        # We can identify overlapping candidate handlers, not inspect arbitrary
        # scripts or prove that a dynamic command rewrites input.
        for group in supplied.get("PreToolUse", []):
            if not isinstance(group, dict):
                raise ValueError("invalid hook group")
            for hook in group.get("hooks", []):
                if isinstance(hook, dict) and hook.get("command"):
                    result["conflicts"].append({"kind": "external_pretool_handler_requires_review",
                                                "matcher": group.get("matcher", "*")})
        result["conflicts"] = result["conflicts"][:32]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("event", "doctor", "replay", "route-preflight"), default="event")
    parser.add_argument("--client", choices=("claude", "codex"), required=True)
    parser.add_argument("--input", type=Path, help="JSONL events for replay; JSON effective inputs for route-preflight")
    parser.add_argument("--settings", type=Path, help="read-only check of an explicitly supplied client settings file")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            print(json.dumps(doctor(args.client, os.environ, settings_path=args.settings)))
            return 0
        if args.command == "route-preflight":
            if args.client != "codex" or not args.input:
                parser.error("route-preflight requires --client codex and --input")
            raw = read_json(args.input)
            report = codex_route_check(**raw)
            print(json.dumps(report))
            # This checks supplied configuration, not native launch/compliance.
            return 1 if report["conflicts"] else 2 if report["unverified"] else 0
        if args.command == "replay":
            if not args.input:
                parser.error("replay requires --input")
            # Offline replay never consumes real receipts or mutates installed
            # runtime state, even when a developer has those env vars set.
            with args.input.open("rb") as stream:
                index, failed = 0, False
                while raw := stream.readline(MAX_INPUT + 1):
                    if index >= 1000 or len(raw) > MAX_INPUT:
                        raise ValueError("replay bound exceeded")
                    event = loads(raw.decode("utf-8"))
                    if normalize(event, args.client) is None:
                        raise ValueError("unsupported replay event")
                    result, error = process(event, args.client, {})
                    failed = failed or error is not None
                    print(json.dumps({"index": index, "result": result, "error": error,
                                      "evidence": "synthetic_replay"}))
                    index += 1
            return 2 if index == 0 or failed else 0
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            raise ValueError("oversized event")
        event = loads(raw.decode("utf-8"))
        result, error = process(event, args.client, os.environ)
        print(json.dumps(result))
        if error:
            print(error, file=sys.stderr)
        return 0
    except Exception:
        print("Assay: invalid or unavailable hook input/configuration; no payload was recorded.", file=sys.stderr)
        # Event type is unknown. A missing/disabled/broken hook is not an
        # enforcement boundary; never claim a protected action was prevented.
        return 1 if args.command == "event" else 2


if __name__ == "__main__":
    raise SystemExit(main())
