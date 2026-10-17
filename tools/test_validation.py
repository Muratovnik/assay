"""Discriminating controls for adapter structure and deterministic source gates."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tools import assay as aa
from tools import catalog_docs as docs
from tools import eval_assets as ev
from tools.test_assay import (
    CATALOG, EXPLICIT_SKILL, README_TABLES, add_explicit_skill, readme_with_rows,
    write_fixture,
)


REAL_SHARED_TEXTS = dict(aa.SHARED_TEXTS)


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

    def test_a_reference_no_link_reaches_fails_the_source_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            skill = root / "skills/route-subagents"
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\nRead [the deep case](references/core.md) when X.\n",
                encoding="utf-8", newline="\n")
            (skill / "references").mkdir()
            (skill / "references/core.md").write_text(
                "See [the sample](deep.md).\n", encoding="utf-8", newline="\n")
            (skill / "references/deep.md").write_text("Deep.\n", encoding="utf-8", newline="\n")
            aa.write_rendered(root)
            problems = aa.check(root)
            self.assertEqual(1, len(problems), problems)
            self.assertTrue(
                problems[0].startswith(
                    "skills/route-subagents/references/deep.md: not linked from "
                    "skills/route-subagents/SKILL.md"
                ),
                problems,
            )
            (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "Read [the sample](references/deep.md) when Y.\n",
                encoding="utf-8", newline="\n")
            aa.write_rendered(root)
            self.assertEqual([], aa.check(root))
            (skill / "references/orphan.md").write_text("Unlinked.\n", encoding="utf-8", newline="\n")
            problems = aa.check(root)
            self.assertEqual(1, len(problems), problems)
            self.assertTrue(
                problems[0].startswith("skills/route-subagents/references/orphan.md: not linked from"),
                problems,
            )


class RegistrationGateTests(unittest.TestCase):
    """A catalogued skill must carry its Codex interface and a row in every README."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        write_fixture(self.root)
        aa.write_rendered(self.root)

    def test_complete_registration_passes(self) -> None:
        self.assertEqual([], aa.check(self.root))

    def test_skill_without_openai_yaml_fails_naming_the_skill(self) -> None:
        (self.root / "skills/route-subagents/agents/openai.yaml").unlink()
        aa.write_rendered(self.root)
        self.assertEqual(
            [
                "skills/route-subagents: missing agents/openai.yaml; "
                "every skill needs its Codex interface"
            ],
            aa.check(self.root),
        )

    def test_readme_without_the_skill_row_fails_naming_readme_and_skill(self) -> None:
        for readme in README_TABLES:
            with self.subTest(readme=readme):
                path = self.root / readme
                complete = path.read_text(encoding="utf-8")
                # The skill stays mentioned in prose: only a table row counts.
                path.write_text(
                    readme_with_rows() + "\nSee route-subagents for delegation.\n",
                    encoding="utf-8",
                    newline="\n",
                )
                problems = aa.check(self.root)
                self.assertEqual(
                    [
                        f"{readme}: skill table has no row for route-subagents "
                        "([route-subagents](skills/route-subagents/SKILL.md))"
                    ],
                    problems,
                )
                path.write_text(complete, encoding="utf-8", newline="\n")
                self.assertEqual([], aa.check(self.root))

    def test_missing_translated_readme_fails(self) -> None:
        (self.root / "README.ru.md").unlink()
        self.assertEqual(
            ["README.ru.md: missing; it must list every catalogued skill"],
            aa.check(self.root),
        )

    def test_added_skill_needs_its_row_in_every_readme(self) -> None:
        write_fixture(self.root, CATALOG + EXPLICIT_SKILL)
        add_explicit_skill(self.root)
        adapter = self.root / "skills/explicit-example/agents/openai.yaml"
        adapter.parent.mkdir()
        adapter.write_text(
            'interface: {default_prompt: "Use $explicit-example"}\n'
            "policy: {allow_implicit_invocation: false}\n",
            encoding="utf-8",
            newline="\n",
        )
        aa.write_rendered(self.root)
        self.assertEqual([], aa.check(self.root))
        path = self.root / "README.zh-CN.md"
        path.write_text(readme_with_rows("route-subagents"), encoding="utf-8", newline="\n")
        problems = aa.check(self.root)
        self.assertEqual(1, len(problems), problems)
        self.assertTrue(problems[0].startswith("README.zh-CN.md: "), problems)
        self.assertIn("explicit-example", problems[0])


class CueTermGateTests(unittest.TestCase):
    """A cue and the trigger part of its description must share the table's terms."""

    SKILL = "skills/route-subagents/SKILL.md"
    RULES = "hooks/activation-rules.toml"

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        write_fixture(self.root)
        self.write_cue("subagents (grants no authority)")
        self.write_description("Route bounded subagent packets after authorized delegation.")
        self.catalog = aa.load_catalog(self.root)

    def write_cue(self, cue: str) -> None:
        path = self.root / self.RULES
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f'schema = 2\n\n[[skills]]\nskill = "skill/route-subagents"\ncue = "{cue}"\n',
            encoding="utf-8",
            newline="\n",
        )

    def write_description(self, description: str) -> None:
        (self.root / self.SKILL).write_text(
            f"---\nname: route-subagents\ndescription: {description}\nlicense: MIT\n---\n\n"
            "# Route subagents\n",
            encoding="utf-8",
            newline="\n",
        )

    def problems(self, *terms: str) -> list[str]:
        return aa.cue_term_problems(self.root, self.catalog, {"route-subagents": terms})

    def test_shared_terms_pass(self) -> None:
        self.assertEqual([], self.problems("subagent", "authori"))

    def test_cue_without_its_term_fails_naming_cue_and_term(self) -> None:
        self.write_cue("handing work to helpers")
        self.assertEqual(
            [
                f"{self.RULES}: cue of route-subagents lacks 'subagent', which the "
                "first sentence of its description names"
            ],
            self.problems("subagent"),
        )

    def test_description_without_the_term_fails_even_when_the_cue_has_it(self) -> None:
        self.write_description("Route bounded packets after authorized delegation.")
        self.assertEqual(
            [
                f"{self.SKILL}: first sentence of the description lacks 'subagent', which "
                "the cue of route-subagents names"
            ],
            self.problems("subagent"),
        )

    def test_matching_ignores_case_and_accepts_a_stem(self) -> None:
        self.write_cue("SUBAGENTS, plans and Release Notes")
        self.write_description("Subagent plans and release notes.")
        self.assertEqual([], self.problems("subagent", "plan", "release note"))

    def test_a_term_is_matched_at_the_start_of_a_word(self) -> None:
        self.write_cue("subagents")
        self.write_description("Route bounded subagent packets.")
        self.assertEqual(2, len(self.problems("agent")))

    def test_use_when_clause_is_the_trigger_part(self) -> None:
        self.write_description(
            "Route subagent packets. Use when the user authorizes delegation; "
            "skip other tickets."
        )
        self.write_cue("subagents with authority")
        self.assertEqual([], self.problems("authori"))
        # The first sentence and the skip half are outside the clause.
        for term, outside in (("subagent", "first sentence"), ("ticket", "skip half")):
            with self.subTest(outside=outside):
                self.write_cue(f"{term}s with authority")
                problems = self.problems(term)
                self.assertEqual(1, len(problems), problems)
                self.assertIn(f"trigger clause of the description lacks '{term}'", problems[0])

    def test_description_without_use_when_is_held_to_its_first_sentence(self) -> None:
        self.write_description(
            "Route bounded subagent packets. Skip tiny work that needs no authority."
        )
        self.write_cue("subagents with authority")
        self.assertEqual([], self.problems("subagent"))
        self.assertEqual(
            [
                f"{self.SKILL}: first sentence of the description lacks 'authori', which "
                "the cue of route-subagents names"
            ],
            self.problems("authori"),
        )

    def test_use_for_and_use_on_open_the_trigger_clause(self) -> None:
        # A description may open its trigger with "Use for" or "Use on"; the
        # first sentence is then outside the clause, as with "Use when".
        self.write_cue("subagent packets")
        for opener in ("Use for", "Use on"):
            with self.subTest(opener=opener):
                self.write_description(f"Route bounded packets. {opener} subagent work; skip the rest.")
                self.assertEqual([], self.problems("subagent"))
                self.assertEqual(1, len(self.problems("packet")))

    def test_catalogued_skill_without_a_table_entry_fails(self) -> None:
        self.assertEqual(
            [
                "tools/assay.py CUE_TERMS: route-subagents has no terms; list the stems "
                "its cue and description must share"
            ],
            aa.cue_term_problems(self.root, self.catalog, {}),
        )
        self.assertEqual(1, len(self.problems()), "an empty term list is no entry")

    def test_entry_for_an_uncatalogued_skill_fails(self) -> None:
        problems = aa.cue_term_problems(
            self.root, self.catalog, {"route-subagents": ("subagent",), "gone": ("x",)}
        )
        self.assertEqual(
            ["tools/assay.py CUE_TERMS: entry for gone, which is not a catalogued skill"],
            problems,
        )

    def test_source_check_runs_the_term_gate(self) -> None:
        aa.write_rendered(self.root)
        with mock.patch.dict(aa.CUE_TERMS, {"route-subagents": ("subagent",)}, clear=True):
            self.assertEqual([], aa.check(self.root))
            self.write_cue("handing work to helpers")
            problems = aa.check(self.root)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("cue of route-subagents lacks 'subagent'", problems[0])

    def test_real_table_catches_a_narrowed_real_cue(self) -> None:
        """The shipped table, against the shipped texts, with one cue cut down."""
        for relative in ("catalog.toml", self.RULES):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((aa.ROOT / relative).read_bytes())
        catalog = aa.load_catalog(self.root)
        for asset in catalog.assets:
            if asset.kind == "skill":
                target = self.root / asset.path / "SKILL.md"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((aa.ROOT / asset.path / "SKILL.md").read_bytes())
        self.assertEqual([], aa.cue_term_problems(self.root, catalog))
        rules = self.root / self.RULES
        text = rules.read_text(encoding="utf-8")
        narrowed = text.replace("architecture, boundaries, contracts or file placement", "file placement")
        self.assertNotEqual(text, narrowed)
        rules.write_text(narrowed, encoding="utf-8", newline="\n")
        problems = aa.cue_term_problems(self.root, catalog)
        self.assertEqual(1, len(problems), problems)
        self.assertTrue(all("cue of software-architecture lacks" in p for p in problems), problems)


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


class SharedTextTests(unittest.TestCase):
    """One source rendered into skills that must each install alone."""

    SOURCE = "skill-sources/editorial-core.md"
    TECHNICAL = "skills/technical-writing/references/editorial-core.md"
    TEXT = "skills/text-writing/references/editorial-core.md"
    # The fixture catalogues one skill, so the copies of a fixture live there.
    COPIES = {
        "technical-writing": "skills/route-subagents/references/technical.md",
        "text-writing": "skills/route-subagents/references/text.md",
    }
    CONTENT = (
        "# Shared\n\n"
        "Both skills read this.\n\n"
        "<!-- only: technical-writing\n"
        "Only technical writing reads this.\n"
        "-->\n"
        "Closing line.\n"
    )

    def setUp(self) -> None:
        patcher = mock.patch.object(aa, "SHARED_TEXTS", {self.SOURCE: self.COPIES})
        patcher.start()
        self.addCleanup(patcher.stop)

    def rendered_root(self, directory: str) -> Path:
        root = Path(directory)
        write_fixture(root)
        # Every reference must be reachable from its SKILL.md, the copies included.
        skill = root / "skills/route-subagents/SKILL.md"
        links = "".join(f"\nRead [{Path(path).stem}](references/{Path(path).name}) when needed.\n"
                        for path in self.COPIES.values())
        skill.write_text(skill.read_text(encoding="utf-8") + links, encoding="utf-8", newline="\n")
        source = root / self.SOURCE
        source.parent.mkdir(parents=True)
        source.write_text(self.CONTENT, encoding="utf-8", newline="\n")
        aa.write_rendered(root)
        return root

    def test_the_repository_copies_are_what_the_source_renders(self) -> None:
        with mock.patch.object(aa, "SHARED_TEXTS", REAL_SHARED_TEXTS):
            self.assertEqual([], [item for item in aa.render_drift(aa.ROOT) if "editorial-core" in item])
        for target in (self.TECHNICAL, self.TEXT):
            with self.subTest(target=target):
                first = (aa.ROOT / target).read_text(encoding="utf-8").splitlines()[0]
                self.assertEqual(
                    f"<!-- Generated from {self.SOURCE} by tools/assay.py render; "
                    "do not edit this file. -->",
                    first,
                )

    def test_a_skill_only_block_reaches_only_its_skill(self) -> None:
        for name in ("technical-writing", "text-writing"):
            with self.subTest(skill=name):
                text = aa.shared_text(
                    self.SOURCE, self.CONTENT.encode(), name, ("technical-writing", "text-writing")
                ).decode()
                self.assertNotIn("only:", text)
                self.assertNotIn("-->\n", text.split("\n", 1)[1])
                self.assertIn("Both skills read this.\n", text)
                self.assertIn("Closing line.\n", text)
                self.assertEqual(
                    name == "technical-writing", "Only technical writing reads this.\n" in text
                )
        repository = (aa.ROOT / self.TEXT).read_text(encoding="utf-8")
        self.assertNotIn("document-design.md", repository)
        self.assertIn(
            "document-design.md#review-the-finished-content",
            (aa.ROOT / self.TECHNICAL).read_text(encoding="utf-8"),
        )

    def test_a_hand_edited_copy_fails_the_check_until_rendered_again(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.rendered_root(directory)
            self.assertEqual([], aa.check(root))
            copy = root / self.COPIES["text-writing"]
            copy.write_bytes(copy.read_bytes().replace(b"Closing", b"Edited"))
            self.assertTrue(any(self.COPIES["text-writing"] in item for item in aa.check(root)))
            aa.write_rendered(root)
            self.assertEqual([], aa.check(root))

    def test_an_edited_source_fails_the_check_until_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.rendered_root(directory)
            source = root / self.SOURCE
            source.write_text(self.CONTENT + "Added.\n", encoding="utf-8", newline="\n")
            drift = aa.check(root)
            for copy in self.COPIES.values():
                self.assertTrue(any(copy in item for item in drift))

    def test_a_copy_without_its_source_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.rendered_root(directory)
            (root / self.SOURCE).unlink()
            self.assertTrue(any("which is missing" in item for item in aa.render_drift(root)))

    def test_malformed_skill_only_blocks_are_refused(self) -> None:
        skills = ("technical-writing", "text-writing")
        for label, content in (
            ("unclosed", "<!-- only: text-writing\nA\n"),
            ("not open", "A\n-->\n"),
            ("nested", "<!-- only: text-writing\n<!-- only: text-writing\n-->\n"),
            ("unknown skill", "<!-- only: no-such-skill\nA\n-->\n"),
        ):
            with self.subTest(case=label), self.assertRaises(aa.ContractError):
                aa.shared_text(self.SOURCE, content.encode(), "text-writing", skills)


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

    def test_every_marked_document_is_checked_and_the_english_one_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            english = root / docs.DOCUMENT
            english.parent.mkdir(parents=True)
            marked = docs.BEGIN + "\nold\n" + docs.END + "\n"
            english.write_text(marked, encoding="utf-8")
            english.write_text(docs.updated(marked, aa.load_catalog(root)), encoding="utf-8")
            self.assertTrue(docs.check(root))

            translated = root / "docs/ru/architecture.md"
            translated.parent.mkdir(parents=True)
            translated.write_text("Опись.\n" + marked, encoding="utf-8")
            self.assertIn(translated, docs.documents(root))
            self.assertFalse(docs.check(root), "a stale translation must fail the gate")

            translated.write_text(docs.updated(translated.read_text(encoding="utf-8"),
                                               aa.load_catalog(root)), encoding="utf-8")
            self.assertTrue(docs.check(root))

            unmarked = root / "docs/ru/install.md"
            unmarked.write_text("Установка без описи.\n", encoding="utf-8")
            self.assertNotIn(unmarked, docs.documents(root))

            english.write_text("no markers here\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                docs.documents(root)


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
        with self.assertRaisesRegex(ValueError, "non-text input"):
            ev.input_case({"id": "X", "prompt": "x", "files": {"a.txt": None}})
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
            for name in ("evidence-research", "code-change"):
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

    def test_skill_identity_and_collection_mismatches_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cases, rubric = self.corpus(Path(directory))
            ev.check_pair(cases, rubric, "evidence-research")
            with self.assertRaisesRegex(ValueError, "skill identity mismatch"):
                ev.check_pair(cases, rubric, "code-change")
            data = ev.load(rubric)
            del data["discovery_cases"]
            rubric.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "collections disagree"):
                ev.check_pair(cases, rubric, "evidence-research")

    def test_refused_preparation_allocates_no_packet(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source" / "method" / "evals"
            source.mkdir(parents=True)
            foreign = base / "foreign"
            foreign.mkdir()
            output = base / "packets"
            output.mkdir()
            method = base / "runtime" / "evidence-research"
            method.mkdir(parents=True)
            (method / "SKILL.md").write_text("method\n", encoding="utf-8")
            cases, _ = self.corpus(source)
            unregistered, _ = self.corpus(foreign, "not-a-paired-skill")
            refusals = (
                ("unknown case", {"cases_path": cases, "case_id": "missing"}),
                ("unsupported inline corpus", {"cases_path": unregistered, "case_id": "E01"}),
                ("duplicate method roots", {"cases_path": cases, "case_id": "E01",
                                            "skill_roots": (method, method)}),
            )
            for message, arguments in refusals:
                with self.subTest(refusal=message):
                    with self.assertRaisesRegex(ValueError, message):
                        ev.prepare(output_parent=output, **arguments)
                    self.assertEqual([], list(output.iterdir()))
            ev.prepare(cases_path=cases, case_id="E01", output_parent=output)
            self.assertEqual(1, len(list(output.iterdir())))


if __name__ == "__main__":
    unittest.main()
