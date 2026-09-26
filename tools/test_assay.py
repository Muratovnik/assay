from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import tomllib

from tools import assay as aa

CATALOG = """schema = 2

[source]
generated_paths = ["tools/__pycache__"]

[[assets]]
id = "skill/route-subagents"
kind = "skill"
path = "skills/route-subagents"
activation = "automatic"
license = "MIT"
attribution = "Demo contributors"
projections = [
  { client = "codex", root = "agents", path = "skills/route-subagents", mode = "link" },
  { client = "claude", root = "claude", path = "skills/route-subagents", mode = "link" },
]

[[assets]]
id = "profile/evidence-reviewer"
kind = "profile"
path = "profiles/evidence-reviewer.json"
activation = "explicit"
license = "MIT"
attribution = "Demo contributors"
projections = [
  { client = "codex", root = "codex", path = "agents/evidence-reviewer.toml", mode = "render" },
  { client = "claude", root = "claude", path = "agents/evidence-reviewer.md", mode = "render" },
]

[[assets]]
id = "profile/official-docs-researcher"
kind = "profile"
path = "profiles/official-docs-researcher.json"
activation = "explicit"
license = "MIT"
attribution = "Demo contributors"
projections = [
  { client = "codex", root = "codex", path = "agents/official-docs-researcher.toml", mode = "render" },
  { client = "claude", root = "claude", path = "agents/official-docs-researcher.md", mode = "render" },
]
"""

EXPLICIT_SKILL = """
[[assets]]
id = "skill/explicit-example"
kind = "skill"
path = "skills/explicit-example"
activation = "explicit"
license = "MIT"
attribution = "Demo contributors"
projections = [
  { client = "codex", root = "agents", path = "skills/explicit-example", mode = "link" },
  { client = "claude", root = "claude", path = "skills/explicit-example", mode = "link" },
]
"""


def profile(name: str, capabilities: list[str]) -> str:
    return (
        json.dumps(
            {
                "schema_version": 1,
                "name": name,
                "description": f"Read-only {name} role.",
                "capabilities": capabilities,
                "instructions": ["Inspect the supplied evidence and do not mutate it."],
            },
            indent=2,
        )
        + "\n"
    )


def write_fixture(root: Path, catalog: str = CATALOG) -> None:
    files = {
        "AGENTS.md": "# Fixture instructions\n",
        "CHANGELOG.md": "# Changelog\n",
        "CLAUDE.md": "@AGENTS.md\n",
        "LICENSE": "MIT\n",
        "README.md": "# Fixture\n",
        "VERSION": "1.0.0\n",
        "catalog.toml": catalog,
        "profiles/evidence-reviewer.json": profile(
            "evidence-reviewer",
            ["workspace-read", "workspace-search", "read-only-oracle"],
        ),
        "profiles/official-docs-researcher.json": profile(
            "official-docs-researcher",
            ["workspace-read", "workspace-search", "primary-web-research"],
        ),
        "skills/route-subagents/SKILL.md": (
            "---\n"
            "name: route-subagents\n"
            "description: Route bounded Codex or Claude subagent packets.\n"
            "license: MIT\n"
            "---\n\n"
            "# Route subagents\n"
        ),
        "skills/route-subagents/agents/openai.yaml": (
            "interface:\n"
            '  display_name: "Route subagents"\n'
            '  short_description: "Route bounded subagent packets safely"\n'
            '  default_prompt: "Use $route-subagents to route this packet."\n'
        ),
        "tools/check.py": "# fixture entry point\n",
    }
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


def add_explicit_skill(root: Path) -> None:
    definition = root / "skills/explicit-example/SKILL.md"
    definition.parent.mkdir(parents=True, exist_ok=True)
    definition.write_text(
        "---\n"
        "name: explicit-example\n"
        "description: Run explicit bounded delivery only when directly invoked.\n"
        "license: MIT\n"
        "---\n\n"
        "# Orchestrated delivery\n",
        encoding="utf-8",
        newline="\n",
    )


def write_claude_explicit_override(
    home: Path, value: object = "user-invocable-only"
) -> Path:
    settings = home / ".claude/settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(
        json.dumps({"skillOverrides": {"explicit-example": value}}, indent=2)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return settings


class AgentAssetsTests(unittest.TestCase):
    def test_byte_exact_declaration_covers_payload_and_nothing_else(self) -> None:
        """A `* -text` directory exempts its payload, never the prose beside it.

        The exemption exists for fixtures that carry CRLF or broken encoding on
        purpose. It must not become a way to smuggle a stray CR into a document
        that merely shares their directory, and it must not reach a directory
        that never declared itself.
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".gitattributes").write_text(
                "* -text\n.gitattributes text eol=lf\nREADME.md text eol=lf\n",
                encoding="utf-8",
            )
            kept = aa.still_text(root)
            self.assertEqual({".gitattributes", "README.md"}, kept)

            plain = root / "plain"
            plain.mkdir()
            self.assertIsNone(aa.still_text(plain))

            (root / ".gitattributes").write_text("*.bin -text\n", encoding="utf-8")
            self.assertIsNone(
                aa.still_text(root),
                "a declaration that is not `* -text` exempts nothing",
            )

    def test_repository_check_and_inventory_are_exact(self) -> None:
        self.assertEqual([], aa.check(aa.ROOT))
        catalog = aa.load_catalog(aa.ROOT)
        self.assertEqual(
            {
                "skill/route-subagents",
                "skill/ui-delivery",
                "skill/product-flow-mapping",
                "skill/independent-audit",
                "skill/skill-evaluation",
                "skill/evidence-research",
                "skill/test-writing",
                "skill/test-audit",
                "skill/code-change",
                "skill/implementation-planning",
                "skill/software-architecture",
                "skill/research-driven-change",
                "skill/technical-writing",
                "skill/text-writing",
                "profile/evidence-reviewer",
                "profile/official-docs-researcher",
            },
            {asset.id for asset in catalog.assets},
        )

    def test_owner_gates_do_not_depend_on_external_skill_creator(self) -> None:
        surfaces = (
            aa.ROOT / "AGENTS.md",
            aa.ROOT / "docs" / "architecture.md",
        )
        for path in surfaces:
            with self.subTest(path=path.relative_to(aa.ROOT)):
                self.assertNotIn("skill-creator", path.read_text(encoding="utf-8"))

    def test_delegation_skills_preserve_authority_and_one_level_depth(self) -> None:
        route = (aa.ROOT / "skills/route-subagents/SKILL.md").read_text(
            encoding="utf-8"
        )
        orchestrated = (
            aa.ROOT / "skills/route-subagents/references/writing-and-integration.md"
        ).read_text(encoding="utf-8")
        operations = (
            aa.ROOT / "skills/ui-delivery/SKILL.md"
        ).read_text(encoding="utf-8")
        orchestrated_words = " ".join(orchestrated.split())
        operations_words = " ".join(operations.split())

        self.assertIn("This skill does not grant permission to delegate", route)
        self.assertIn("parallelism alone is never permission to spawn", route)
        self.assertIn("Only the primary/root agent may spawn subagents", route)
        self.assertIn("worker must not spawn additional agents", route)
        self.assertNotIn("Delegate a concrete packet when parallelism", route)

        self.assertIn("Only that primary may spawn subagents", orchestrated_words)
        self.assertIn("Every worker must be told not to spawn", orchestrated_words)
        self.assertIn(
            "This automatic skill does not authorize delegation", operations_words
        )
        self.assertIn(
            "otherwise the primary runs it directly", operations_words
        )

    def test_current_catalog_needs_no_retired_activation_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            self.assertEqual([], aa.activation_prerequisites(aa.ROOT, home))
            settings = home / ".claude/settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text('{"skillOverrides":{"retired-example":"disabled"}}', encoding="utf-8")
            self.assertEqual([], aa.activation_prerequisites(aa.ROOT, home))
            aa.install_links(aa.ROOT, home)
            self.assertFalse((home / ".agents/skills/orchestrated-delivery").exists())
            self.assertFalse((home / ".claude/skills/avoid-ai-design").exists())
            self.assertTrue((home / ".agents/skills/route-subagents/SKILL.md").is_file())
            aa.uninstall_links(aa.ROOT, home)

    def test_catalog_rejects_compatibility_paths_and_system_targets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(
                root,
                CATALOG.replace(
                    'root = "agents", path = "skills/route-subagents"',
                    'root = "codex", path = "skills/route-subagents"',
                    1,
                ),
            )
            with self.assertRaisesRegex(aa.ContractError, "expected root/path/mode"):
                aa.load_catalog(root)

            write_fixture(
                root,
                CATALOG.replace(
                    'path = "skills/route-subagents", mode = "link"',
                    'path = "skills/.system", mode = "link"',
                    1,
                ),
            )
            with self.assertRaisesRegex(aa.ContractError, "never managed"):
                aa.load_catalog(root)

    def test_evidence_reviewer_adapters_can_run_a_read_only_oracle(self) -> None:
        catalog = aa.load_catalog(aa.ROOT)
        asset = next(
            item for item in catalog.assets if item.id == "profile/evidence-reviewer"
        )
        source = (aa.ROOT / asset.path).read_bytes()
        codex = aa.render_profile(source, asset, "codex").decode("utf-8")
        claude = aa.render_profile(source, asset, "claude").decode("utf-8")
        self.assertEqual("read-only", tomllib.loads(codex)["sandbox_mode"])
        self.assertIn("You may run the caller's declared read-only oracle", codex)
        tool_line = next(line for line in claude.splitlines() if line.startswith("tools: "))
        self.assertEqual(
            {"Read", "Grep", "Glob", "ToolSearch", "Bash", "Skill"},
            {value.strip() for value in tool_line.removeprefix("tools: ").split(",")},
        )
        self.assertIn("permissionMode: plan", claude)

    def test_plan_is_native_deterministic_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, home = base / "source", base / "home"
            root.mkdir()
            home.mkdir()
            write_fixture(root)
            before = sorted(
                path.relative_to(base).as_posix() for path in base.rglob("*")
            )
            first = aa.plan_document(root, home)
            second = aa.plan_document(root, home)
            after = sorted(
                path.relative_to(base).as_posix() for path in base.rglob("*")
            )
            self.assertEqual(first, second)
            self.assertEqual(before, after)
            targets = {entry["target"] for entry in first["entries"]}
            self.assertIn(str(home / ".agents/skills/route-subagents"), targets)
            self.assertIn(str(home / ".claude/skills/route-subagents"), targets)
            self.assertNotIn(".codex\\skills", "\n".join(targets))
            self.assertNotIn(".codex/skills", "\n".join(targets))
            claude_skill = next(
                entry
                for entry in first["entries"]
                if entry["asset"] == "skill/route-subagents"
                and entry["client"] == "claude"
            )
            self.assertEqual(
                str(home / ".agents/skills/route-subagents"), claude_skill["source"]
            )
            self.assertTrue(
                all(
                    entry["rollback"]["operation"] == "remove-only-if-exact"
                    for entry in first["entries"]
                )
            )

    def test_explicit_claude_skill_requires_user_invocable_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, home = base / "source", base / "home"
            root.mkdir()
            home.mkdir()
            write_fixture(root, CATALOG + EXPLICIT_SKILL)
            add_explicit_skill(root)

            plan = aa.plan_document(root, home)
            self.assertEqual(2, plan["schema"])
            self.assertEqual("missing", plan["prerequisites"][0]["state"])
            self.assertIn("PREREQUISITE MISSING", "\n".join(aa.format_plan(plan)))
            with self.assertRaisesRegex(
                aa.ContractError, "unmet activation prerequisites"
            ):
                aa.install_links(root, home)
            self.assertTrue(
                all(not aa.lexists(entry.target) for entry in aa.native_plan(root, home))
            )

            write_claude_explicit_override(home, "enabled")
            self.assertEqual(
                "mismatch", aa.activation_prerequisites(root, home)[0]["state"]
            )
            with self.assertRaisesRegex(
                aa.ContractError, "expected 'user-invocable-only'"
            ):
                aa.install_links(root, home)

            settings = write_claude_explicit_override(home)
            self.assertEqual(
                "exact", aa.activation_prerequisites(root, home)[0]["state"]
            )
            aa.install_links(root, home)
            settings.unlink()
            removed = aa.uninstall_links(root, home)
            self.assertTrue(all(action.startswith("REMOVED ") for action in removed))

    def test_explicit_claude_prerequisite_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, home = base / "source", base / "home"
            root.mkdir()
            home.mkdir()
            write_fixture(root, CATALOG + EXPLICIT_SKILL)
            add_explicit_skill(root)
            settings = home / ".claude/settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text(
                '{"skillOverrides":{"explicit-example":"user-invocable-only",'
                '"explicit-example":"enabled"}}\n',
                encoding="utf-8",
            )
            prerequisite = aa.activation_prerequisites(root, home)[0]
            self.assertEqual("invalid", prerequisite["state"])
            self.assertIn("duplicate JSON key", prerequisite["detail"])
            with self.assertRaisesRegex(
                aa.ContractError, "unmet activation prerequisites"
            ):
                aa.install_links(root, home)

    def test_install_and_uninstall_touch_only_exact_entries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, home = base / "source&A%Z", base / "home&A%Z"
            root.mkdir()
            home.mkdir()
            write_fixture(root)
            system = home / ".codex/skills/.system/owned.txt"
            system.parent.mkdir(parents=True)
            system.write_text("codex-owned\n", encoding="utf-8")

            actions = aa.install_links(root, home)
            self.assertTrue(all(action.startswith("INSTALLED ") for action in actions))
            plan = aa.native_plan(root, home)
            self.assertTrue(all(aa.entry_state(entry)[0] == "exact" for entry in plan))
            self.assertEqual("codex-owned\n", system.read_text(encoding="utf-8"))
            self.assertTrue(
                aa.same_path(
                    aa.link_destination(home / ".claude/skills/route-subagents"),
                    home / ".agents/skills/route-subagents",
                )
            )
            self.assertTrue(
                all(
                    action.startswith("NOOP ")
                    for action in aa.install_links(root, home)
                )
            )

            removed = aa.uninstall_links(root, home)
            self.assertTrue(all(action.startswith("REMOVED ") for action in removed))
            self.assertTrue(all(not aa.lexists(entry.target) for entry in plan))
            self.assertTrue((root / "skills/route-subagents/SKILL.md").is_file())
            self.assertEqual("codex-owned\n", system.read_text(encoding="utf-8"))

    def test_client_selection_keeps_the_link_chain_whole(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, home = base / "source", base / "home"
            root.mkdir()
            home.mkdir()
            write_fixture(root)
            codex_skill = home / ".agents/skills/route-subagents"
            claude_skill = home / ".claude/skills/route-subagents"
            claude_profile = home / ".claude/agents/evidence-reviewer.md"

            self.assertEqual(
                {"codex"},
                {entry.client for entry in aa.native_plan(root, home, ["codex"])},
            )
            with self.assertRaisesRegex(aa.ContractError, "unknown client selection"):
                aa.native_plan(root, home, ["cursor"])
            with self.assertRaisesRegex(aa.ContractError, "broken link chain"):
                aa.install_links(root, home, ["claude"])
            self.assertFalse(aa.lexists(claude_skill))

            aa.install_links(root, home)
            with self.assertRaisesRegex(aa.ContractError, "broken link chain"):
                aa.uninstall_links(root, home, ["codex"])
            self.assertTrue(aa.lexists(codex_skill))

            removed = aa.uninstall_links(root, home, ["claude"])
            self.assertTrue(all(action.startswith("REMOVED ") for action in removed))
            self.assertFalse(aa.lexists(claude_skill))
            self.assertFalse(aa.lexists(claude_profile))
            self.assertTrue(
                all(
                    aa.entry_state(entry)[0] == "exact"
                    for entry in aa.native_plan(root, home, ["codex"])
                )
            )

            aa.install_links(root, home, ["claude"])
            self.assertTrue(
                all(
                    aa.entry_state(entry)[0] == "exact"
                    for entry in aa.native_plan(root, home)
                )
            )

    def test_codex_only_selection_skips_claude_prerequisites(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, home = base / "source", base / "home"
            root.mkdir()
            home.mkdir()
            write_fixture(root, CATALOG + EXPLICIT_SKILL)
            add_explicit_skill(root)

            self.assertEqual([], aa.plan_document(root, home, ["codex"])["prerequisites"])
            actions = aa.install_links(root, home, ["codex"])
            self.assertTrue(all(action.startswith("INSTALLED ") for action in actions))
            self.assertFalse((home / ".claude").exists())
            options = aa.parser().parse_args(
                ["uninstall-links", "--client", "claude", "--client", "codex"]
            )
            self.assertEqual(["claude", "codex"], options.clients)

    def test_install_preflight_refuses_a_real_directory_without_partial_writes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, home = base / "source", base / "home"
            root.mkdir()
            home.mkdir()
            write_fixture(root)
            foreign = home / ".claude/skills/route-subagents"
            foreign.mkdir(parents=True)
            (foreign / "foreign.txt").write_text("keep\n", encoding="utf-8")
            with self.assertRaisesRegex(aa.ContractError, "refused foreign targets"):
                aa.install_links(root, home)
            self.assertFalse(aa.lexists(home / ".agents/skills/route-subagents"))
            self.assertEqual(
                "keep\n", (foreign / "foreign.txt").read_text(encoding="utf-8")
            )

    def test_install_preflight_refuses_a_foreign_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, home, foreign_source = (
                base / "source",
                base / "home",
                base / "foreign",
            )
            root.mkdir()
            home.mkdir()
            foreign_source.mkdir()
            write_fixture(root)
            target = home / ".agents/skills/route-subagents"
            target.parent.mkdir(parents=True)
            os.symlink(foreign_source, target, target_is_directory=True)
            with self.assertRaisesRegex(aa.ContractError, "refused foreign targets"):
                aa.install_links(root, home)
            self.assertTrue(aa.same_path(aa.link_destination(target), foreign_source))
            self.assertFalse((home / ".codex/agents/evidence-reviewer.toml").exists())

    def test_linked_parent_is_rejected_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, home, foreign_parent = (
                base / "source",
                base / "home",
                base / "foreign",
            )
            root.mkdir()
            home.mkdir()
            foreign_parent.mkdir()
            write_fixture(root)
            os.symlink(foreign_parent, home / ".agents", target_is_directory=True)
            with self.assertRaisesRegex(aa.ContractError, "ancestor"):
                aa.install_links(root, home)
            self.assertFalse((home / ".codex/agents/evidence-reviewer.toml").exists())
            self.assertEqual([], list(foreign_parent.iterdir()))

    def test_uninstall_refuses_modified_adapter_before_removing_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, home = base / "source", base / "home"
            root.mkdir()
            home.mkdir()
            write_fixture(root)
            aa.install_links(root, home)
            adapter = home / ".codex/agents/evidence-reviewer.toml"
            adapter.write_text("locally changed\n", encoding="utf-8")
            with self.assertRaisesRegex(aa.ContractError, "refused foreign targets"):
                aa.uninstall_links(root, home)
            self.assertTrue(aa.lexists(home / ".agents/skills/route-subagents"))
            self.assertEqual("locally changed\n", adapter.read_text(encoding="utf-8"))

    def test_install_failure_after_creation_removes_every_new_exact_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, home = base / "source", base / "home"
            root.mkdir()
            home.mkdir()
            write_fixture(root)
            real_create = aa.create_entry
            calls = 0

            def fail_second(entry: aa.PlannedEntry, selected_home: Path) -> None:
                nonlocal calls
                calls += 1
                real_create(entry, selected_home)
                if calls == 2:
                    raise OSError("injected post-creation failure")

            with (
                mock.patch.object(aa, "create_entry", side_effect=fail_second),
                self.assertRaisesRegex(OSError, "injected post-creation failure"),
            ):
                aa.install_links(root, home)
            self.assertTrue(
                all(
                    not aa.lexists(entry.target) for entry in aa.native_plan(root, home)
                )
            )

    def test_adapter_publish_failure_removes_its_hardlink_and_temporary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, home = base / "source", base / "home"
            root.mkdir()
            home.mkdir()
            write_fixture(root)
            real_link = os.link

            def fail_after_link(source: Path, target: Path) -> None:
                real_link(source, target)
                raise OSError("injected post-link failure")

            with (
                mock.patch.object(os, "link", side_effect=fail_after_link),
                self.assertRaisesRegex(OSError, "injected post-link failure"),
            ):
                aa.install_links(root, home)
            self.assertTrue(
                all(
                    not aa.lexists(entry.target) for entry in aa.native_plan(root, home)
                )
            )
            self.assertEqual([], list(home.rglob("*.tmp")))

    def test_uninstall_failure_recreates_each_entry_already_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, home = base / "source", base / "home"
            root.mkdir()
            home.mkdir()
            write_fixture(root)
            aa.install_links(root, home)
            real_remove = aa.remove_entry
            calls = 0

            def fail_second(entry: aa.PlannedEntry) -> None:
                nonlocal calls
                calls += 1
                real_remove(entry)
                if calls == 2:
                    raise OSError("injected post-removal failure")

            with (
                mock.patch.object(aa, "remove_entry", side_effect=fail_second),
                self.assertRaisesRegex(OSError, "injected post-removal failure"),
            ):
                aa.uninstall_links(root, home)
            self.assertTrue(
                all(
                    aa.entry_state(entry)[0] == "exact"
                    for entry in aa.native_plan(root, home)
                )
            )


if __name__ == "__main__":
    unittest.main()
