"""Offline hook protocol and packaged-command tests, not model compliance tests."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/route-subagents/scripts/skill_reminder.py"
# Bounds a hung shell, not the hook budget asserted below: a cold Windows
# PowerShell 5 start on a hosted runner can take 5 s on its own.
SHELL_WIRING_TIMEOUT = 30


class ReminderTests(unittest.TestCase):
    def invoke(self, payload, config=None):
        # The developer's own routing configuration must not decide the result.
        env = {k: v for k, v in os.environ.items() if k != "ASSAY_ROUTING_CONFIG"}
        if config is not None:
            env["ASSAY_ROUTING_CONFIG"] = str(config)
        return subprocess.run(
            [sys.executable, "-I", "-B", str(SCRIPT)],
            input=payload, capture_output=True, timeout=5, env=env,
        )

    def output(self, event, config=None):
        result = self.invoke(json.dumps(event).encode(), config)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(b"", result.stderr)
        return json.loads(result.stdout)

    def test_required_claude_routing_leaves_claude_launches_to_the_guard(self):
        spawn = {"hook_event_name": "PreToolUse", "tool_input": {"prompt": "work"}}
        start = {"hook_event_name": "SessionStart", "source": "startup"}
        with tempfile.TemporaryDirectory() as tmp:
            def config(name, value):
                path = Path(tmp) / name
                path.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")
                return path
            required = {"schema_version": 3, "client": "claude", "pipeline": {"mode": "required"}}
            silent = config("required.json", required)
            for tool in ("Agent", "Task"):
                with self.subTest(tool=tool):
                    self.assertEqual({}, self.output({**spawn, "tool_name": tool}, silent))
            # Codex launches and the session reminder are not the guard's to answer.
            self.assertIn("hookSpecificOutput", self.output({**spawn, "tool_name": "spawn_agent"}, silent))
            self.assertIn("hookSpecificOutput", self.output(start, silent))
            for name, value in (("evidence.json", {**required, "pipeline": {"mode": "evidence-only"}}),
                                ("codex.json", {**required, "client": "codex"}),
                                ("v2.json", {**required, "schema_version": 2}),
                                ("broken.json", "{not json")):
                with self.subTest(config=name):
                    self.assertIn("hookSpecificOutput", self.output({**spawn, "tool_name": "Agent"}, config(name, value)))
            self.assertIn("hookSpecificOutput", self.output({**spawn, "tool_name": "Agent"}, Path(tmp) / "missing.json"))

    def test_session_reminder_survives_every_supported_restart(self):
        for source in ("startup", "resume", "clear", "compact", "fork"):
            with self.subTest(source=source):
                output = self.output({"hook_event_name": "SessionStart", "source": source})
                self.assertEqual({"hookSpecificOutput"}, set(output))
                context = output["hookSpecificOutput"]
                self.assertEqual({"hookEventName", "additionalContext"}, set(context))
                self.assertEqual("SessionStart", context["hookEventName"])
                text = context["additionalContext"]
                self.assertIn("does not authorize delegation", text)
                self.assertIn("workers must not spawn further agents", text)
                # Without configured routing the base reminder stays short but
                # keeps the planning step for any wording of a subagent request;
                # the launch reminder carries the routing checklist.
                self.assertIn("route-subagents before substantial solo work", text)
                self.assertNotIn("Before every authorized subagent launch", text)
                self.assertLessEqual(len(re.findall(r"\.\s", text + " ")), 3)
                self.assertLess(len(text), 360)

    def test_configured_routing_adds_delegation_guidance_at_session_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "routing.json"
            config.write_text("{}", encoding="utf-8")
            text = self.output({"hook_event_name": "SessionStart", "source": "startup"}, config)[
                "hookSpecificOutput"]["additionalContext"]
        self.assertTrue(text.startswith("Assay is installed."))
        self.assertIn("Before every authorized subagent launch", text)
        self.assertEqual(1, text.count("before substantial solo work"))
        self.assertIn("does not authorize delegation", text)
        self.assertLess(len(text), 1000)

    def test_delegation_aliases_remind_without_permission_or_argument_changes(self):
        for tool in ("spawn_agent", "Agent", "Task"):
            with self.subTest(tool=tool):
                output = self.output({
                    "hook_event_name": "PreToolUse", "tool_name": tool,
                    "tool_input": {"model": "chosen-by-user", "prompt": "PRIVATE_SENTINEL"},
                    "transcript_path": "PRIVATE_SENTINEL", "cwd": "PRIVATE_SENTINEL",
                })
                self.assertEqual({"hookSpecificOutput"}, set(output))
                context = output["hookSpecificOutput"]
                self.assertEqual({"hookEventName", "additionalContext"}, set(context))
                self.assertEqual("PreToolUse", context["hookEventName"])
                self.assertIn("route-subagents", context["additionalContext"])
                self.assertIn("model", context["additionalContext"])
                self.assertIn("effort", context["additionalContext"])
                self.assertNotIn("PRIVATE_SENTINEL", json.dumps(output))
                self.assertLess(len(context["additionalContext"]), 1000)

    def test_unrelated_or_incomplete_events_are_silent(self):
        for event in (
            {}, {"hook_event_name": "SessionStart"},
            {"hook_event_name": "SessionStart", "source": "unrecognized"},
            {"hook_event_name": "PostToolUse", "tool_name": "Agent"},
            {"hook_event_name": "PreToolUse", "tool_name": "AgentStatus"},
            {"hook_event_name": "PreToolUse", "tool_name": "send_message"},
            {"hook_event_name": ["PreToolUse"], "tool_name": {}},
        ):
            with self.subTest(event=event):
                self.assertEqual({}, self.output(event))

    def test_bad_input_reports_nonblocking_error_without_echo(self):
        for raw in (b"PRIVATE_SENTINEL", b"[]", b"null", b"\xff", b" " * (1024 * 1024 + 1)):
            with self.subTest(size=len(raw)):
                result = self.invoke(raw)
                self.assertEqual(1, result.returncode)
                self.assertEqual(b"", result.stdout)
                self.assertIn(b"invalid or oversized", result.stderr)
                self.assertNotIn(b"PRIVATE_SENTINEL", result.stderr)

    def test_packaged_matchers_only_cover_reminder_and_guard_boundaries(self):
        for client, filename in (("claude", "hooks.json"), ("codex", "codex.json")):
            hooks = json.loads((ROOT / "hooks" / filename).read_text())["hooks"]
            common = {"SessionStart", "UserPromptSubmit", "PreToolUse", "SubagentStart", "SubagentStop", "PostToolUse", "SessionEnd"}
            extra = {"PermissionDenied", "PostToolUseFailure"} if client == "claude" else {"PostCompact"}
            self.assertEqual(common | extra, set(hooks))

            def commands(event, value):
                return [hook["command"] for rule in hooks[event] if re.search(rule.get("matcher") or "", value)
                        for hook in rule["hooks"]]

            unified = commands("SessionStart", "startup")
            self.assertEqual(1, len(unified))
            self.assertIn("hooks/runtime/cli.py", unified[0])
            self.assertIn("'" + client + "'", unified[0])
            self.assertEqual(unified, commands("UserPromptSubmit", ""))
            # Neither client starts a process for ordinary tool invocations.
            for tool in ("Bash", "Read", "Edit", "Write", "Skill", "AgentStatus", "send_message", "wait",
                         "mcp__example__search", "mcp__benchmark-routing__routing_status"):
                with self.subTest(client=client, tool=tool):
                    self.assertEqual([], commands("PreToolUse", tool))
            for tool in (("Agent", "Task") if client == "claude" else ("Agent", "spawn_agent")):
                self.assertEqual(unified, commands("PreToolUse", tool))
            self.assertEqual(unified if client == "claude" else [], commands("PreToolUse", "SubagentHandback"))
            for tool in ("mcp__benchmark-routing__prepare_routing", "mcp__plugin_assay_routing__authorize_routing_launch"):
                self.assertEqual(unified, commands("PreToolUse", tool))
            for event in ("SubagentStart", "SubagentStop"):
                self.assertEqual(unified, commands(event, "assay-general-purpose-0123456789abcdef"))
                for agent_type in ("Explore", "general-purpose", ""):
                    self.assertEqual([], commands(event, agent_type))
            for source in ("startup", "resume", "clear", "compact"):
                self.assertEqual(unified, commands("SessionStart", source))
            self.assertEqual(unified if client == "claude" else [], commands("SessionStart", "fork"))
            self.assertEqual([], commands("SessionStart", "shutdown"))
            for event, rules in hooks.items():
                for rule in rules:
                    self.assertEqual(1, len(rule["hooks"]))
                    for hook in rule["hooks"]:
                        self.assertEqual("command", hook["type"])
                        timeout_limit = 3 if client == "codex" and event == "SessionEnd" else 5
                        self.assertLessEqual(hook["timeout"], timeout_limit)

    def test_guard_matcher_names_exactly_the_routing_operations(self):
        sys.path.insert(0, str(SCRIPT.parent))
        try:
            from route_evidence.pipeline_config import ROUTING_TOOLS
            from tools import assay
        finally:
            sys.path.remove(str(SCRIPT.parent))
        self.assertEqual(ROUTING_TOOLS, assay.ROUTING_OPERATIONS)

    def test_packaged_command_from_other_cwd_with_space_and_shell_characters(self):
        # A local fixture checks shell/path wiring without trusting a plugin or
        # launching a client/model. Both clients supply this environment key.
        scratch = ROOT / ".cache"
        self.assertTrue(scratch.resolve().is_relative_to(ROOT.resolve()))
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="reminder-", dir=scratch) as directory:
            base = Path(directory)
            plugin = base / "plugin space & apostrophe'"
            # Package the actual installed runtime and its existing owner, not
            # a stand-in that accidentally lets a broken command look correct.
            shutil.copytree(ROOT / "hooks", plugin / "hooks", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(ROOT / "skills", plugin / "skills", ignore=shutil.ignore_patterns("__pycache__", "evals"))
            shutil.copyfile(ROOT / "catalog.toml", plugin / "catalog.toml")
            before = sorted(str(path.relative_to(base)) for path in base.rglob("*"))
            command = json.loads((ROOT / "hooks/hooks.json").read_text())["hooks"]["SessionStart"][0]["hooks"][0]["command"]
            shells = (
                [None, ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command"]]
                if os.name == "nt" else [["/bin/sh", "-c"]]
            )
            for shell in shells:
                with self.subTest(shell=shell):
                    result = subprocess.run(
                        command if shell is None else [*shell, command],
                        shell=shell is None, cwd=base,
                        env={**{k: v for k, v in os.environ.items() if not k.startswith("ASSAY_") and k not in {"PLUGIN_DATA", "CLAUDE_PLUGIN_DATA"}},
                             "CLAUDE_PLUGIN_ROOT": str(plugin)},
                        input=b'{"hook_event_name":"SessionStart","source":"compact"}',
                        capture_output=True, timeout=SHELL_WIRING_TIMEOUT,
                    )
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual("SessionStart", json.loads(result.stdout)["hookSpecificOutput"]["hookEventName"])
            self.assertEqual(before, sorted(str(path.relative_to(base)) for path in base.rglob("*")))


if __name__ == "__main__":
    unittest.main()
