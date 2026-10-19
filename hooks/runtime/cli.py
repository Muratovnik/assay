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
from runtime import state, routing_binding, skill_gate, sources, branches, midturn
from route_evidence.client_capabilities import contract, codex_route_check
from route_evidence.core import RetiredConfiguration, loads
from route_evidence import host_observations
from route_evidence import route_table
from route_evidence.service import load_config
from routing_hook import explicit_launch, deny
from skill_reminder import reminder

MAX_INPUT = 1024 * 1024
# The refusal carries the rule, because an open session may hold an older skill.
NESTED_SPAWN = ("only the primary agent launches agents, so delegation stays one level deep. "
                "Do this part of the work yourself; if a step needs a separate agent, finish your packet and "
                "name that step in your report so the primary can route and launch it.")


# Options of the removed feedback recorder. A configuration that still names one is
# refused with the list, not with the generic unknown-option error.
REMOVED_OPTIONS = frozenset({"record_events", "feedback_capture", "feedback_trigger"})


class RemovedOptions(ValueError):
    """The hook configuration names an option that no longer exists; the message says which."""


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
    removed = sorted(set(raw) & REMOVED_OPTIONS)
    if removed:
        raise RemovedOptions("Assay: hook options " + ", ".join(removed) + " were removed together with "
                             "feedback capture and event recording; delete them from the hook configuration.")
    if set(raw) - {"disabled_rules", "disabled_skills", "state_dir", "skill_note_form"}:
        raise ValueError("unknown hook option")
    value = {"disabled_rules": [], "disabled_skills": [], "skill_note_form": "note",
             "state_dir": environment.get("PLUGIN_DATA") or environment.get("CLAUDE_PLUGIN_DATA"), **raw}
    for key in ("disabled_rules", "disabled_skills"):
        if not isinstance(value[key], list) or any(not isinstance(v, str) for v in value[key]):
            raise ValueError("invalid disabled rules or skills")
    if not isinstance(value["skill_note_form"], str) or value["skill_note_form"] not in midturn.FORMS:
        raise ValueError("invalid skill note form")
    if value["state_dir"] is not None and (not isinstance(value["state_dir"], str) or not Path(value["state_dir"]).is_absolute()):
        raise ValueError("hook state directory must be absolute")
    return value


def routing_config(environment):
    """The routing configuration the launch check applies, or None without one.

    `ASSAY_ROUTING_CONFIG` names it directly; otherwise the plugin's routing
    binding does, so an owner who set up the binding gets the check without
    another setting.
    """
    location = environment.get("ASSAY_ROUTING_CONFIG")
    if location:
        return load_config(Path(location))
    binding = routing_binding.configuration(environment)
    return load_config(Path(binding["config"])) if binding else None


def explicit_routes(event, client, environment):
    """The launch check of a configured routing configuration.

    With a route table every spawn must follow its declared class, and a spawn
    the table does not check is pointed at it instead of the generic launch
    reminder; without one a Claude spawn must still name both settings. A
    Claude spawn from inside a subagent is refused before either check: only
    the primary routes. Codex hook input does not say which agent calls, so its
    depth stays with `agents.max_depth`. A missing, unreadable or retired
    configuration refuses a recognized launch; no configuration keeps ordinary
    delegation.
    """
    spec = route_table.SPAWN.get(client)
    if (spec is None or event.get("hook_event_name") != "PreToolUse"
            or event.get("tool_name") not in spec["tools"]):
        return {}
    try:
        config = routing_config(environment)
        if config is None:
            return {}
        if client == "claude" and event.get("agent_id") is not None and config.get("client") == client:
            return deny(NESTED_SPAWN)
        table = config.get("routes")
        if table is None:
            return explicit_launch(event, config) if client == "claude" else {}
        mode = config["pipeline"]
        if config.get("client") != client:
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
    except RetiredConfiguration as exc:
        # The message names keys and file names only, never paths or payloads.
        return deny(str(exc))
    except Exception:
        return deny("routing configuration could not be validated; restore the configured route table before delegation")


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
        protected = reviewer_boundary(event, environment, clock=clock) or explicit_routes(event, client, environment)
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
        loaded = []
        if client == "claude" and rules.skill_gate and settings["state_dir"]:
            # Records skill loads on PreToolUse; on Stop it can hold a turn to
            # the skills it announced. A guard reply keeps priority.
            names = {rule["skill"].split("/", 1)[1] for rule in rules}
            gate = skill_gate.apply(event, client, names, settings["state_dir"],
                                    **({"clock": clock} if clock else {}))
            if gate and not protected:
                return gate, None
            if event["hook_event_name"] == "UserPromptSubmit":
                # The check names skills already loaded, so the model can stay quiet about them.
                loaded = skill_gate.loaded(event, client, names, settings["state_dir"],
                                           **({"clock": clock} if clock else {}))
        name = event["hook_event_name"]
        enabled = {rule["skill"].split("/", 1)[1] for rule in rules}
        if client == "claude" and not protected:
            # How a source was read, not which skill applies; the skill gate's reply keeps priority.
            note = (sources.fetched(event, settings["state_dir"], **({"clock": clock} if clock else {}))
                    if name == "PostToolUse" and rules.fetch_note
                    else sources.stopped(event) if name in {"Stop", "SubagentStop"} and rules.read_claims
                    # A tool call that shows a skill this session has not loaded; a routing reply and the
                    # launch reminder own their PreToolUse, so this check stays silent there.
                    else midturn.checked(event, rules.midturn_rules, enabled, settings["state_dir"],
                                         form=settings["skill_note_form"], **({"clock": clock} if clock else {}))
                    if name == "PreToolUse" and rules.midturn_rules and not legacy else {})
            # A stop continues at most once: a contradicted read claim goes first.
            if not note and name in {"Stop", "SubagentStop"} and rules.branch_rules:
                note = branches.stopped(event, rules.branch_rules, enabled)
            if note:
                return note, None
        decision = ({"rule_ids": [], "context": ""} if protected
                    else evaluate(event, rules, client=client, loaded=loaded))
        if legacy:
            decision["context"] = legacy["hookSpecificOutput"]["additionalContext"]
        if settings["state_dir"]:
            kwargs = {"clock": clock} if clock else {}
            decision = state.apply(event, client, decision, rules, fingerprint, settings["state_dir"],
                                   outcome=outcome, loaded=loaded, **kwargs)
        if protected:
            return protected, None  # One voice; no competing permission/argument writers.
        if decision["context"]:
            return {"hookSpecificOutput": {"hookEventName": event["hook_event_name"],
                                          "additionalContext": decision["context"]}}, None
        return {}, None
    except RemovedOptions as exc:
        return protected or legacy, str(exc)
    except Exception:
        return protected or legacy, "Assay: optional hints unavailable; routing decision and basic reminders retained. Run hooks doctor."


OBSERVED_EVENTS = frozenset({"PreToolUse", "PostToolUse", "PostToolUseFailure", "SubagentStop"})


def observe(event, client, environment, *, clock=None):
    """Record what a Claude launch's alias and effort ran as, in the binding's cache directory."""
    name = event.get("hook_event_name")
    if (client != "claude" or name not in OBSERVED_EVENTS
            or (name != "SubagentStop" and event.get("tool_name") not in route_table.SPAWN["claude"]["tools"])):
        return
    binding = routing_binding.configuration(environment)
    if binding is not None:
        host_observations.observe(event, binding["cache_dir"], **({"clock": clock} if clock else {}))


def process(event, client, environment, *, root=ROOT, clock=None):
    result, error = _process(event, client, environment, root=root, clock=clock)
    try:
        # A refused launch never ran, so it leaves no observation.
        if result.get("hookSpecificOutput", {}).get("permissionDecision") != "deny":
            observe(event, client, environment, clock=clock)
    except RetiredConfiguration as exc:
        error = "\n".join(part for part in (error, "Assay: " + str(exc)) if part)
    except Exception:
        diagnostic = "Assay: host observations unavailable; hook decision retained. Check the routing binding."
        error = "\n".join(part for part in (error, diagnostic) if part)
    return result, error


def doctor(client, environment, *, root=ROOT, settings_path=None):
    settings = options(environment)
    rules, fingerprint = load_rules(root, disabled_rules=settings["disabled_rules"], disabled_skills=settings["disabled_skills"])
    binding = routing_binding.configuration(environment)
    config = routing_config(environment) or {}
    result = {"capabilities": contract(client, config.get("pipeline", {}).get("host")),
              "rules": [r["id"] for r in rules], "rules_fingerprint": fingerprint,
              "skill_check": rules.skill_check,
              "skill_note_form": settings["skill_note_form"],
              "prompt_parser_available": importlib.util.find_spec("markdown_it") is not None,
              "state_configured": settings["state_dir"] is not None,
              "hooks_trusted": "unknown",
              "native_execution": "unverified", "model_compliance": "unverified",
              "routing_binding_found": binding is not None,
              "routing_config_found": bool(config),
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
    except RemovedOptions as exc:
        print(str(exc), file=sys.stderr)
        return 1 if args.command == "event" else 2
    except RetiredConfiguration as exc:
        print("Assay: " + str(exc), file=sys.stderr)
        return 1 if args.command == "event" else 2
    except Exception:
        print("Assay: invalid or unavailable hook input/configuration; no payload was recorded.", file=sys.stderr)
        # Event type is unknown. A missing/disabled/broken hook is not an
        # enforcement boundary; never claim a protected action was prevented.
        return 1 if args.command == "event" else 2


if __name__ == "__main__":
    raise SystemExit(main())
