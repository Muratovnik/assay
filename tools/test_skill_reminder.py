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
    def invoke(self, payload):
        return subprocess.run(
            [sys.executable, "-I", "-B", str(SCRIPT)],
            input=payload, capture_output=True, timeout=5,
        )

    def output(self, event):
        result = self.invoke(json.dumps(event).encode())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(b"", result.stderr)
        return json.loads(result.stdout)

    def test_session_reminder_survives_every_supported_restart(self):
        for source in ("startup", "resume", "clear", "compact", "fork"):
            with self.subTest(source=source):
                output = self.output({"hook_event_name": "SessionStart", "source": source})
                self.assertEqual({"hookSpecificOutput"}, set(output))
                context = output["hookSpecificOutput"]
                self.assertEqual({"hookEventName", "additionalContext"}, set(context))
                self.assertEqual("SessionStart", context["hookEventName"])
                self.assertIn("route-subagents", context["additionalContext"])
                self.assertIn("does not authorize delegation", context["additionalContext"])
                self.assertLess(len(context["additionalContext"]), 1000)

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
        hooks = json.loads((ROOT / "hooks/hooks.json").read_text())["hooks"]
        self.assertEqual({"SessionStart", "PreToolUse", "PermissionDenied", "SubagentStart", "SubagentStop",
                          "PostToolUse", "PostToolUseFailure", "SessionEnd"}, set(hooks))

        def commands(event, value):
            # An omitted matcher matches every value of that event.
            return [hook["command"] for rule in hooks[event] if re.search(rule.get("matcher") or "", value)
                    for hook in rule["hooks"]]

        reminder = [h["command"] for h in hooks["SessionStart"][0]["hooks"] if "skill_reminder" in h["command"]]
        guard = [h["command"] for h in hooks["SessionStart"][0]["hooks"] if "routing_hook" in h["command"]]
        self.assertEqual((1, 1), (len(reminder), len(guard)))
        # Ordinary tools must not start any hook process for any plugin user.
        for tool in ("Bash", "Read", "Edit", "Write", "Skill", "AgentStatus", "send_message", "wait",
                     "mcp__example__search", "mcp__benchmark-routing__routing_status"):
            with self.subTest(tool=tool):
                self.assertEqual([], commands("PreToolUse", tool))
        self.assertEqual(reminder, commands("PreToolUse", "spawn_agent"))
        for tool in ("Agent", "Task"):
            self.assertEqual(reminder + guard, commands("PreToolUse", tool))
        for tool in ("SubagentHandback", "mcp__benchmark-routing__prepare_routing",
                     "mcp__plugin_assay_routing__authorize_routing_launch"):
            self.assertEqual(guard, commands("PreToolUse", tool))
        for event in ("SubagentStart", "SubagentStop"):
            self.assertEqual(guard, commands(event, "assay-general-purpose-0123456789abcdef"))
            for agent_type in ("Explore", "general-purpose", ""):
                self.assertEqual([], commands(event, agent_type))
        for source in ("startup", "resume", "clear", "compact", "fork"):
            self.assertEqual(reminder + guard, commands("SessionStart", source))
        self.assertEqual([], commands("SessionStart", "shutdown"))
        for rules in hooks.values():
            for rule in rules:
                for hook in rule["hooks"]:
                    self.assertEqual("command", hook["type"])
                    self.assertLessEqual(hook["timeout"], 5)

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
            target = plugin / SCRIPT.relative_to(ROOT)
            target.parent.mkdir(parents=True)
            shutil.copyfile(SCRIPT, target)
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
                        env=dict(os.environ, CLAUDE_PLUGIN_ROOT=str(plugin)),
                        input=b'{"hook_event_name":"SessionStart","source":"compact"}',
                        capture_output=True, timeout=SHELL_WIRING_TIMEOUT,
                    )
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual("SessionStart", json.loads(result.stdout)["hookSpecificOutput"]["hookEventName"])
            self.assertEqual(before, sorted(str(path.relative_to(base)) for path in base.rglob("*")))


if __name__ == "__main__":
    unittest.main()
