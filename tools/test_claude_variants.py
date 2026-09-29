"""Client-specific artifacts preserve neutral profiles and user-owned files."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/route-subagents" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import os
import yaml
from route_evidence.claude_agents import MANIFEST, generate, guard_command, internal_templates, remove, resolve_variant
from route_evidence.core import EvidenceError, timestamp
from route_evidence.pipeline_config import settings
from route_evidence.pipeline_store import PipelineStore


class VariantTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = settings({"pipeline": {"agents_dir": str(self.root / "agents"),
            "state_dir": str(self.root / "state"),
            "variants": [{"profile": "general-purpose", "model": "fixture-model", "effort": e} for e in ("low", "high")]}})

    def test_generation_is_idempotent_and_efforts_have_distinct_files(self):
        first = generate(self.config, {})
        before = {p.name: p.read_bytes() for p in (self.root / "agents").iterdir()}
        second = generate(self.config, {})
        self.assertEqual(first, second)
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.root / "agents").iterdir()})
        self.assertEqual(len({v["file"] for v in first["variants"]}), 2)
        for record in first["variants"]:
            self.assertIn("effort: " + record["effort"], (self.root / "agents" / record["file"]).read_text())
        self.assertFalse(first["root_settings_changed"])
        self.assertFalse(first["discovery_verified"])

    def test_modified_owned_file_refuses_without_overwrite(self):
        first = generate(self.config, {})
        path = self.root / "agents" / first["variants"][0]["file"]
        changed = path.read_bytes() + b"\nUSER MODIFICATION\n"
        path.write_bytes(changed)
        with self.assertRaises(EvidenceError):
            generate(self.config, {}, prune=True)
        self.assertEqual(path.read_bytes(), changed)

    def test_foreign_collision_refuses_without_claiming_ownership(self):
        first = generate(self.config, {})
        (self.root / "agents" / MANIFEST).unlink()
        with self.assertRaisesRegex(EvidenceError, "foreign"):
            generate(self.config, {})
        self.assertTrue((self.root / "agents" / first["variants"][0]["file"]).exists())
        self.assertFalse((self.root / "agents" / MANIFEST).exists())

    def test_source_revision_keeps_active_retired_ownership_until_pruned(self):
        first = generate(self.config, {})
        old = first["variants"][0]
        template = internal_templates()["general-purpose"] + b"\nNew bounded instruction.\n"
        second = generate(self.config, {"general-purpose": template}, prune=True, active_names={old["name"]})
        manifest = json.loads((self.root / "agents" / MANIFEST).read_text())
        self.assertEqual(manifest["retired"], [old])
        current = resolve_variant(self.config, "general-purpose", old, environment={})
        self.assertNotEqual(current["name"], old["name"])
        self.assertTrue((self.root / "agents" / old["file"]).exists())
        third = generate(self.config, {"general-purpose": template}, prune=True)
        self.assertIn(old["name"], third["removed"])
        self.assertFalse((self.root / "agents" / old["file"]).exists())
        self.assertNotEqual(first["variants"], second["variants"])

    def test_foreign_agent_is_not_touched_by_pruning(self):
        generate(self.config, {})
        other = self.root / "agents" / "user-reviewer.md"
        other.write_text("User-owned reviewer", encoding="utf-8")
        generate(self.config, {}, prune=True)
        self.assertEqual(other.read_text(), "User-owned reviewer")

    def test_environment_override_is_rejected_without_changing_environment(self):
        record = generate(self.config, {})["variants"][0]
        for env in ({"CLAUDE_CODE_EFFORT_LEVEL": "max"}, {"CLAUDE_CODE_SUBAGENT_MODEL": "other"}):
            before = dict(env)
            with self.assertRaisesRegex(EvidenceError, "override"):
                resolve_variant(self.config, "general-purpose", record, environment=env)
            self.assertEqual(env, before)

    def test_unknown_profile_fails_before_creating_artifacts(self):
        self.config["variants"][0]["profile"] = "invented-reviewer"
        with self.assertRaisesRegex(EvidenceError, "unknown"):
            generate(self.config, {})
        self.assertFalse((self.root / "agents").exists())

    def test_partial_write_failure_rolls_back_created_files(self):
        with patch("route_evidence.claude_agents.atomic_write", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                generate(self.config, {})
        self.assertEqual(list((self.root / "agents").glob("*.md")), [])

    def test_linked_directory_is_rejected(self):
        target = self.root / "real"
        target.mkdir()
        try:
            (self.root / "agents").symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation unavailable")
        with self.assertRaisesRegex(EvidenceError, "linked"):
            generate(self.config, {})
        self.assertEqual(list(target.iterdir()), [])

    def test_generator_cli_uses_existing_neutral_profile_renderer(self):
        config = self.root / "config.json"
        from tools.assay import load_catalog, profile_assets
        profile = profile_assets(load_catalog(ROOT))[0]
        pipeline = {**self.config, "variants": [{"profile": profile.name, "model": "fixture-model", "effort": "low"}]}
        config.write_text(json.dumps({"schema_version": 3, "client": "claude", "pipeline": pipeline,
            "inventory": {"available": [{"model": "fixture-model", "efforts": ["low"]}], "observed_at": timestamp(time.time())}}))
        source_before = (ROOT / profile.path).read_bytes()
        proc = subprocess.run([sys.executable, "-B", str(ROOT / "tools/assay.py"), "claude-routes", "--config", str(config)],
            text=True, capture_output=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((ROOT / profile.path).read_bytes(), source_before)
        record = json.loads(proc.stdout)["variants"][0]
        text = (self.root / "agents" / record["file"]).read_text()
        self.assertIn("permissionMode: plan", text)
        self.assertIn("source-sha256:", text)
        self.assertIn("effort: low", text)

    def test_database_expiry_bound_and_link_guards(self):
        clock = [time.time()]
        store = PipelineStore(self.root / "state", clock=lambda: clock[0])
        with store.transaction() as tx:
            tx.put("receipt", "a", {"private": "short-lived"}, clock[0] + 5)
        clock[0] += 6
        with store.transaction() as tx:
            self.assertIsNone(tx.get("receipt", "a"))
            with self.assertRaises(EvidenceError):
                tx.put("receipt", "b", {}, clock[0])

    def test_prune_manifest_failure_restores_removed_bytes_and_old_manifest(self):
        generate(self.config, {})
        before = {p.name: p.read_bytes() for p in (self.root / "agents").iterdir() if p.name != ".assay-routing-v2.lock"}
        template = internal_templates()["general-purpose"] + b"\nChanged template.\n"
        with patch("route_evidence.claude_agents.atomic_write", side_effect=OSError("manifest failure")):
            with self.assertRaises(OSError):
                generate(self.config, {"general-purpose": template}, prune=True)
        after = {p.name: p.read_bytes() for p in (self.root / "agents").iterdir() if p.name != ".assay-routing-v2.lock"}
        self.assertEqual(before, after)

    def test_second_prune_delete_failure_rolls_back_first_deletion(self):
        first = generate(self.config, {})
        directory = self.root / "agents"
        before = {p.name: p.read_bytes() for p in directory.iterdir() if p.name != ".assay-routing-v2.lock"}
        original_unlink = Path.unlink
        target = first["variants"][1]["file"]
        def fail_one(path, *args, **kwargs):
            if path.name == target:
                raise OSError("unlink denied")
            return original_unlink(path, *args, **kwargs)
        template = internal_templates()["general-purpose"] + b"\nChanged template.\n"
        with patch.object(Path, "unlink", fail_one):
            with self.assertRaises(OSError):
                generate(self.config, {"general-purpose": template}, prune=True)
        after = {p.name: p.read_bytes() for p in directory.iterdir() if p.name != ".assay-routing-v2.lock"}
        self.assertEqual(before, after)

    def test_v2_migration_preserves_source_and_policy_and_requires_explicit_mode_change(self):
        from route_evidence.advisor_config import migrate_config
        from route_evidence.service import load_config
        source, dest = self.root / "old.json", self.root / "new.json"
        content = {"schema_version": 2, "client": "claude", "preferences": {"quality_loss_pp": 3},
                   "advisor": {"enabled": False}, "telemetry": {"mode": "off"}}
        source.write_text(json.dumps(content))
        before = source.read_bytes()
        report = migrate_config(source, dest)
        upgraded = load_config(dest)
        # The default keeps the existing workflow; required routing is opt-in.
        self.assertEqual(report["pipeline_mode"], "evidence-only")
        self.assertEqual(upgraded["pipeline"]["mode"], "evidence-only")
        self.assertFalse(upgraded["advisor"]["enabled"])
        self.assertEqual(upgraded["preferences"], content["preferences"])
        self.assertEqual(source.read_bytes(), before)
        with self.assertRaises(FileExistsError):
            migrate_config(source, dest)
        required = self.root / "required.json"
        self.assertTrue(migrate_config(source, required, mode="required")["setup_required"])
        self.assertEqual(load_config(required)["pipeline"]["mode"], "required")

    def frontmatter(self, record):
        text = (self.root / "agents" / record["file"]).read_text(encoding="utf-8")
        return yaml.safe_load(text[4:].partition("\n---\n")[0])

    def test_generated_definitions_check_their_own_tool_calls(self):
        script = SCRIPTS / "routing_hook.py"
        guarded = generate(self.config, {}, guard=guard_command(script))["variants"][0]
        hook = self.frontmatter(guarded)["hooks"]["PreToolUse"][-1]
        self.assertEqual(hook["matcher"], ".*")
        command = hook["hooks"][0]["command"]
        self.assertIn("'--scope', 'agent'", command)
        self.assertIn(str(script.resolve()).encode("utf-8").hex(), command)
        # The checked hook is part of the immutable identity of the definition.
        self.assertNotEqual(guarded["name"], generate({**self.config, "agents_dir": str(self.root / "other")}, {})["variants"][0]["name"])
        # The embedded command runs from any directory through the platform shell.
        event = b'{"hook_event_name":"PreToolUse","session_id":"s","agent_id":"a","tool_name":"Read","tool_input":{}}'
        environment = {k: v for k, v in os.environ.items() if k != "ASSAY_ROUTING_CONFIG"}
        result = subprocess.run(command, shell=True, cwd=self.root, env=environment, input=event,
                                capture_output=True, timeout=30)
        self.assertEqual((result.returncode, result.stdout.strip()), (0, b"{}"), result.stderr)

    def test_existing_user_definition_becomes_a_template_and_stays_unchanged(self):
        source = self.root / "user" / "translator.md"
        source.parent.mkdir()
        source.write_text("---\nname: translator\ndescription: Translate one packet.\ntools: Read, Edit\n---\n\nTranslate only the named files.\n", encoding="utf-8")
        before = source.read_bytes()
        config = self.root / "config.json"
        pipeline = {**self.config, "agent_templates": {"translator": str(source)},
                    "variants": [{"profile": "translator", "model": "fixture-model", "effort": "low"}]}
        document = {"schema_version": 3, "client": "claude", "pipeline": pipeline,
                    "inventory": {"available": [{"model": "fixture-model", "efforts": ["low"]}], "observed_at": timestamp(time.time())}}
        config.write_text(json.dumps(document))
        proc = subprocess.run([sys.executable, "-B", str(ROOT / "tools/assay.py"), "claude-routes", "--config", str(config)],
            text=True, capture_output=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        record = json.loads(proc.stdout)["variants"][0]
        metadata = self.frontmatter(record)
        self.assertTrue(record["name"].startswith("assay-translator-"))
        self.assertEqual((metadata["model"], metadata["effort"], metadata["tools"]), ("fixture-model", "low", "Read, Edit"))
        self.assertIn("Translate only the named files.", (self.root / "agents" / record["file"]).read_text(encoding="utf-8"))
        self.assertEqual(source.read_bytes(), before)
        document["pipeline"]["agent_templates"] = {"evidence-reviewer": str(source)}
        config.write_text(json.dumps(document))
        proc = subprocess.run([sys.executable, "-B", str(ROOT / "tools/assay.py"), "claude-routes", "--config", str(config)],
            text=True, capture_output=True, timeout=30)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("agent_template_name_conflict", proc.stdout + proc.stderr)

    def test_remove_uninstalls_owned_definitions_and_keeps_modified_or_active_ones(self):
        first = generate(self.config, {})
        directory = self.root / "agents"
        modified, active = (directory / first["variants"][0]["file"]), first["variants"][1]["name"]
        modified.write_bytes(modified.read_bytes() + b"\nUSER NOTE\n")
        foreign = directory / "user-reviewer.md"
        foreign.write_text("User-owned reviewer", encoding="utf-8")
        report = remove(self.config, active_names={active})
        self.assertEqual(report["removed"], [])
        self.assertEqual(set(report["kept"]), {first["variants"][0]["name"], active})
        report = remove(self.config)
        self.assertEqual(report["removed"], [active])
        self.assertTrue(modified.exists())
        self.assertEqual(foreign.read_text(), "User-owned reviewer")
        modified.unlink()
        self.assertEqual(remove(self.config)["kept"], [])
        self.assertFalse((directory / MANIFEST).exists())
        self.assertEqual(sorted(p.name for p in directory.glob("*.md")), ["user-reviewer.md"])

    def test_cli_removal_needs_no_runtime_state(self):
        generate(self.config, {})
        config = self.root / "config.json"
        pipeline = {k: v for k, v in self.config.items() if k != "state_dir"}
        config.write_text(json.dumps({"schema_version": 3, "client": "claude", "pipeline": pipeline}))
        proc = subprocess.run([sys.executable, "-B", str(ROOT / "tools/assay.py"), "claude-routes", "--config", str(config), "--remove"],
            text=True, capture_output=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(json.loads(proc.stdout)["removed"]), 2)
        self.assertEqual(list((self.root / "agents").glob("*.md")), [])

    def test_deleted_definition_ends_ownership_without_blocking_regeneration(self):
        first = generate(self.config, {})
        path = self.root / "agents" / first["variants"][0]["file"]
        path.unlink()
        self.assertEqual(generate(self.config, {}), first)
        self.assertTrue(path.exists())

    @unittest.skipUnless(os.name == "nt", "directory junctions are a Windows reparse point")
    def test_junction_ancestor_is_rejected_on_the_oldest_supported_python(self):
        target, link = self.root / "junction-target", self.root / "junction"
        target.mkdir()
        created = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, timeout=30)
        if created.returncode != 0:
            self.skipTest("junction creation unavailable")
        self.addCleanup(os.rmdir, link)  # removes only the link, never its target
        config = {**self.config, "agents_dir": str(link / "agents")}
        with self.assertRaisesRegex(EvidenceError, "linked"):
            generate(config, {})
        self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
