"""Discriminating controls for adapter structure and deterministic source gates."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import assay as aa
from tools import catalog_docs as docs
from tools import eval_assets as ev
from tools.test_assay import CATALOG, EXPLICIT_SKILL, write_fixture, add_explicit_skill


class AdapterStructureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "adapter.yaml"
        self.explicit = aa.Asset("skill/explicit-example", "skill", "skills/explicit-example",
                                 "explicit-example", "explicit", "MIT", "test", ())

    def check_text(self, text: str, *, automatic: bool = False) -> list[str]:
        self.path.write_text(text, encoding="utf-8")
        asset = self.explicit
        if automatic:
            from dataclasses import replace
            asset = replace(asset, activation="automatic")
        return aa.openai_adapter_problems(self.path, asset, self.root)

    def test_valid_yaml_forms_have_the_same_structured_policy(self) -> None:
        for text in (
            'interface:\n  default_prompt: "Use $explicit-example"\npolicy:\n  allow_implicit_invocation: false\n',
            'interface: {default_prompt: "Use $explicit-example"}\npolicy: {allow_implicit_invocation: false}\n',
            'interface:\n  default_prompt: >-\n    Use $explicit-example\n    for this task.\npolicy:\n  allow_implicit_invocation: false # explicit\n',
        ):
            with self.subTest(text=text):
                self.assertEqual([], self.check_text(text))

    def test_rejects_misplaced_or_ambiguous_policy(self) -> None:
        prompt = 'interface:\n  default_prompt: "Use $explicit-example"\n'
        for suffix in (
            "  allow_implicit_invocation: false\n", "allow_implicit_invocation: false\n", "",
            'policy:\n  allow_implicit_invocation: "false"\n',
            "policy:\n  allow_implicit_invocation: 0\n", "policy: []\n", "policy: null\n",
            "policy:\n  allow_implicit_invocation: yes\n", "policy:\n  allow_implicit_invocation: off\n",
            "policy:\n  allow_implicit_invocation: false\n  allow_implicit_invocation: true\n",
            "policy: {allow_implicit_invocation: false}\npolicy: {}\n",
            "policy: {allow_implicit_invocation: true}\n",
            "policy: {allow_implicit_invocation: false, other: true}\n",
        ):
            with self.subTest(suffix=suffix):
                self.assertTrue(self.check_text(prompt + suffix))

    def test_wrong_prompt_location_and_prefix_are_rejected(self) -> None:
        for text in (
            'default_prompt: "Use $explicit-example"\npolicy: {allow_implicit_invocation: false}\n',
            'interface: {default_prompt: "Use $explicit-example-other"}\npolicy: {allow_implicit_invocation: false}\n',
            'interface: {default_prompt: 12}\npolicy: {allow_implicit_invocation: false}\n',
            'interface: {default_prompt: "Use $explicit-example", default_prompt: "duplicate"}\n',
        ):
            with self.subTest(text=text):
                self.assertTrue(self.check_text(text))

    def test_aliases_and_non_data_tags_are_rejected_without_execution(self) -> None:
        for text in ("a: &a {b: 1}\npolicy: *a\n", "!!python/object:builtins.object {}\n", "[1, 2]\n", "a: [\n"):
            with self.subTest(text=text):
                self.assertTrue(self.check_text(text))

    def test_automatic_default_and_missing_explicit_adapter(self) -> None:
        self.assertEqual([], self.check_text('interface: {default_prompt: "Use $explicit-example"}\n', automatic=True))
        write_fixture(self.root, CATALOG + EXPLICIT_SKILL)
        add_explicit_skill(self.root)
        self.path.unlink()
        self.assertTrue(any("explicit activation requires" in item for item in aa.check(self.root)))
        adapter = self.root / "skills/explicit-example/agents/openai.yaml"
        adapter.parent.mkdir()
        adapter.write_text('interface: {default_prompt: "Use $explicit-example"}\npolicy: {allow_implicit_invocation: false}\n', encoding="utf-8", newline="\n")
        aa.write_rendered(self.root)
        self.assertEqual([], aa.check(self.root))

    def test_loader_does_not_change_other_yaml_consumers(self) -> None:
        import yaml
        before = yaml.safe_load("v: yes")
        aa.openai_adapter_document("v: yes")
        self.assertEqual(before, yaml.safe_load("v: yes"))


class SourceGateTests(unittest.TestCase):
    def test_pinned_gate_zipapp_is_read_as_bytes_not_source_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            zipapp = root / ".github" / "relkit.pyz"
            zipapp.parent.mkdir(parents=True)
            zipapp.write_bytes(bytes([0x50, 0x4B, 0x03, 0x04, 0xFF, 0x00]) + b" no final newline")
            aa.write_rendered(root)
            self.assertEqual([], aa.check(root))

    def test_other_tracked_binary_content_still_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            (root / "notes.md").write_bytes(bytes([0xFF, 0x00, 0x0A]))
            self.assertTrue(any("notes.md" in problem for problem in aa.check(root)))


class SkillMetadataTests(unittest.TestCase):
    def test_every_published_skill_states_the_catalog_licence(self) -> None:
        catalog = aa.load_catalog(aa.ROOT)
        skills = [asset for asset in catalog.assets if asset.kind == "skill"]
        self.assertTrue(skills)
        for asset in skills:
            with self.subTest(skill=asset.name):
                metadata = aa.frontmatter(aa.ROOT / asset.path / "SKILL.md")
                self.assertEqual(asset.license, metadata.get("license"))

    def test_a_missing_or_wrong_licence_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            catalog = aa.load_catalog(root)
            asset = next(a for a in catalog.assets if a.kind == "skill")
            path = root / asset.path / "SKILL.md"
            declared = path.read_bytes().decode("utf-8").split(chr(10))
            self.assertEqual([], aa.skill_problems(path, asset, root))

            without = [line for line in declared if not line.startswith("license:")]
            path.write_bytes(chr(10).join(without).encode("utf-8"))
            self.assertTrue(any("license" in p for p in aa.skill_problems(path, asset, root)))

            wrong = [line.replace("MIT", "Apache-2.0") if line.startswith("license:") else line
                     for line in declared]
            path.write_bytes(chr(10).join(wrong).encode("utf-8"))
            self.assertTrue(any("license" in p for p in aa.skill_problems(path, asset, root)))


class RenderedClientFilesTests(unittest.TestCase):
    def test_every_manifest_states_the_source_version(self) -> None:
        version = aa.parse_version(aa.ROOT)
        documents = aa.rendered_documents(aa.ROOT)
        carriers = [
            ".claude-plugin/plugin.json",
            ".claude-plugin/marketplace.json",
            ".codex-plugin/plugin.json",
            ".cursor-plugin/plugin.json",
            "gemini-extension.json",
        ]
        for relative in carriers:
            with self.subTest(manifest=relative):
                document = json.loads(documents[relative].decode("utf-8"))
                found = json.dumps(document)
                self.assertIn(version, found)

    def test_the_index_lists_exactly_the_catalogued_skills(self) -> None:
        catalog = aa.load_catalog(aa.ROOT)
        index = aa.rendered_documents(aa.ROOT)["skills/README.md"].decode("utf-8")
        names = [asset.name for asset in catalog.assets if asset.kind == "skill"]
        self.assertTrue(names)
        for name in names:
            with self.subTest(skill=name):
                self.assertIn(f"]({name}/SKILL.md)", index)
        self.assertEqual(len(names), index.count("/SKILL.md)"))

    def test_claude_plugin_points_at_the_rendered_profile_adapters(self) -> None:
        documents = aa.rendered_documents(aa.ROOT)
        plugin = json.loads(documents[".claude-plugin/plugin.json"].decode("utf-8"))
        catalog = aa.load_catalog(aa.ROOT)
        profiles = [a for a in catalog.assets if a.kind == "profile"]
        self.assertTrue(profiles)
        declared = plugin["agents"]
        self.assertEqual(len(profiles), len(declared))
        for asset in profiles:
            with self.subTest(profile=asset.name):
                entry = f"./adapters/claude/agents/{asset.name}.md"
                self.assertIn(entry, declared)
                self.assertIn(entry.lstrip("./"), documents)

    def test_drift_is_reported_and_repaired(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            self.assertTrue(aa.render_drift(root))
            aa.write_rendered(root)
            self.assertEqual([], aa.render_drift(root))

            manifest = root / ".claude-plugin" / "plugin.json"
            manifest.write_bytes(manifest.read_bytes().replace(b"assay", b"edited"))
            drift = aa.render_drift(root)
            self.assertTrue(any(".claude-plugin/plugin.json" in item for item in drift))

            aa.write_rendered(root)
            self.assertEqual([], aa.render_drift(root))

    def test_a_version_bump_reaches_every_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            aa.write_rendered(root)
            self.assertEqual([], aa.render_drift(root))
            (root / "VERSION").write_bytes(b"9.9.9\n")
            drift = aa.render_drift(root)
            self.assertTrue(any(".claude-plugin/plugin.json" in item for item in drift))
            self.assertTrue(any(".codex-plugin/plugin.json" in item for item in drift))


class CatalogDocumentTests(unittest.TestCase):
    def test_detects_drift_and_preserves_surrounding_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            path = root / docs.DOCUMENT
            path.parent.mkdir(parents=True)
            original = "History stays.\n" + docs.BEGIN + "\nold\n" + docs.END + "\nTail stays.\n"
            path.write_text(original, encoding="utf-8")
            self.assertFalse(docs.check(root))
            rendered = docs.updated(original, aa.load_catalog(root))
            self.assertTrue(rendered.startswith("History stays.\n"))
            self.assertTrue(rendered.endswith("\nTail stays.\n"))
            self.assertIn("~/.agents/skills/route-subagents", rendered)
            self.assertIn("~/.claude/agents/evidence-reviewer.md", rendered)
            path.write_text(rendered, encoding="utf-8")
            self.assertTrue(docs.check(root))
            self.assertEqual(rendered, docs.updated(rendered, aa.load_catalog(root)))
            with self.assertRaises(ValueError):
                docs.updated(rendered + docs.BEGIN, aa.load_catalog(root))


class EvaluationDataTests(unittest.TestCase):
    def test_verifier_cli_leaves_source_unchanged_with_bytecode_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("verify_packet.py", "prepare_case.py"):
                (root / name).write_bytes((ev.ROOT / "skills/independent-audit/evals" / name).read_bytes())
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            loaded = subprocess.run([sys.executable, "-c",
                "import runpy, sys; sys.dont_write_bytecode = False; sys.pycache_prefix = None; "
                "sys.path.insert(0, sys.argv[1]); sys.argv = [sys.argv[1] + '/verify_packet.py', '--help']; "
                "runpy.run_path(sys.argv[0], run_name='__main__')", str(root)],
                capture_output=True, text=True)
            self.assertEqual(0, loaded.returncode, loaded.stderr)
            after = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(before, after, "Starting the verifier must not write into canonical source")

    def test_loading_packet_helper_leaves_source_unchanged_with_bytecode_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ("tools/eval_assets.py", "skills/independent-audit/evals/prepare_case.py"):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ev.ROOT / relative).read_bytes())
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            loaded = subprocess.run([sys.executable, "-c",
                "import runpy, sys; sys.dont_write_bytecode = False; sys.pycache_prefix = None; "
                "helper = runpy.run_path(sys.argv[1])['audit_tools'](); "
                "assert callable(helper.verify_packet)", str(root / "tools/eval_assets.py")],
                capture_output=True, text=True)
            self.assertEqual(0, loaded.returncode, loaded.stderr)
            after = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(before, after, "Loading the helper must not write into canonical source")

    def corpus(self, root: Path, name: str = "evidence-research") -> tuple[Path, Path]:
        cases = root / "cases.json"
        rubric = root / "rubric.json"
        cases.write_text(json.dumps({"schema_version": 1, "skill_name": name,
                                    "cases": [{"id": "E01", "prompt": "Inspect inputs.", "files": {"a.txt": "data\n"}}],
                                    "discovery_cases": [{"id": "D1", "prompt": "A bounded question."}]}), encoding="utf-8")
        rubric.write_text(json.dumps({"schema_version": 1, "skill_name": name,
                                     "cases": [{"id": "E01", "assess": ["private grading canary"]}],
                                     "discovery_cases": [{"id": "D1", "expected_route": name}]}), encoding="utf-8")
        return cases, rubric

    def test_case_rubric_alignment_and_duplicate_controls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases, rubric = self.corpus(root)
            ev.check_pair(cases, rubric, "evidence-research")
            data = ev.load(rubric)
            data["cases"][0]["id"] = "other"
            rubric.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "IDs disagree"):
                ev.check_pair(cases, rubric, "evidence-research")
            data = ev.load(cases)
            data["cases"].append(data["cases"][0])
            cases.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate case"):
                ev.check_pair(cases, rubric, "evidence-research")
            cases.write_text('{"cases": [], "cases": []}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON"):
                ev.load(cases)

    def test_discovery_and_trigger_collections_are_checked_and_materialized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source" / "method" / "evals"
            source.mkdir(parents=True)
            output = base / "packets"
            output.mkdir()
            for collection in ("discovery_cases", "triggers"):
                cases, rubric = self.corpus(source)
                for path in (cases, rubric):
                    data = ev.load(path)
                    data[collection] = data.pop("discovery_cases")
                    path.write_text(json.dumps(data), encoding="utf-8")
                ev.check_pair(cases, rubric, "evidence-research")
                packet, retained = ev.prepare(cases_path=cases, case_id="D1", collection=collection, output_parent=output)
                ev.audit_tools().verify_packet(packet, retained)
                self.assertEqual("A bounded question.\n", (packet / "prompt.txt").read_text(encoding="utf-8"))
                data = ev.load(rubric)
                data[collection][0]["id"] = "wrong"
                rubric.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "IDs disagree"):
                    ev.check_pair(cases, rubric, "evidence-research")

    def test_rejects_unsafe_input_paths_and_grading_keys(self) -> None:
        for name in ("../x", "/x", "a//b", "C:/x", "a\\b", "NUL.txt", "name.", "a:stream", "a\0b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                ev.input_case({"id": "X", "prompt": "x", "files": {name: "data"}})
        for files in ({"a": "x", "A": "y"}, {"a": "x", "a/b": "y"}):
            with self.subTest(files=files), self.assertRaises(ValueError):
                ev.input_case({"id": "X", "prompt": "x", "files": files})
        with self.assertRaises(ValueError):
            ev.input_case({"id": "X", "prompt": "x", "expected_output": "canary"})

    def test_two_inline_consumers_reuse_frozen_packet_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source" / "method" / "evals"
            source.mkdir(parents=True)
            output = base / "packets"
            output.mkdir()
            method = base / "runtime" / "evidence-research"
            (method / "references").mkdir(parents=True)
            (method / "SKILL.md").write_text("method\n", encoding="utf-8")
            (method / "references" / "detail.md").write_text("detail\n", encoding="utf-8")
            (method / "evals").mkdir()
            (method / "evals" / "rubric.json").write_text("never-copy-me", encoding="utf-8")
            for name in ("evidence-research", "code-maintenance"):
                with self.subTest(name=name):
                    cases, _ = self.corpus(source, name)
                    packet, retained = ev.prepare(cases_path=cases, case_id="E01", output_parent=output,
                                                  skill_roots=(method,))
                    ev.audit_tools().verify_packet(packet, retained)
                    text = "".join(p.read_text(encoding="utf-8") for p in packet.rglob("*") if p.is_file())
                    self.assertNotIn("private grading canary", text)
                    self.assertNotIn("never-copy-me", text)
                    self.assertEqual("data\n", (packet / "inputs/a.txt").read_text(encoding="utf-8"))
                    (packet / "inputs/a.txt").write_text("tampered", encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "Packet drift"):
                        ev.audit_tools().verify_packet(packet, retained)
            with self.assertRaisesRegex(ValueError, "outside source"):
                ev.prepare(cases_path=cases, case_id="E01", output_parent=source)


if __name__ == "__main__":
    unittest.main()
