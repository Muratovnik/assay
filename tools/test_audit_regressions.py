from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tools import assay as aa
from tools.skill_resources import selection_problems
from tools.test_assay import write_fixture
from tools.test_skill_resources import skill


class AuditRegressionTests(unittest.TestCase):
    def test_multiline_description_is_one_escaped_table_cell(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            path = root / "skills/route-subagents/SKILL.md"
            path.write_text(
                "---\nname: route-subagents\ndescription: |\n"
                "  Inspect A | B\n  and other consumers.\nlicense: MIT\n---\n",
                encoding="utf-8", newline="\n",
            )
            index = aa.skills_index(root, aa.load_catalog(root)).decode("utf-8")
            self.assertIn("Inspect A \\| B and other consumers.", index)
            self.assertEqual(1, sum("[route-subagents](" in row for row in index.splitlines()))

    def test_source_gate_allows_catalog_without_skills(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            path = root / "catalog.toml"
            text = path.read_text()
            start = text.index('[[assets]]\nid = "skill/route-subagents"')
            end = text.index('[[assets]]\nid = "profile/', start)
            path.write_text(text[:start] + text[end:], encoding="utf-8", newline="\n")
            shutil.rmtree(root / "skills/route-subagents")
            aa.write_rendered(root)
            self.assertEqual([], aa.check(root))

    def test_present_file_cannot_impersonate_optional_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill(root, "first", "[peer](../second)", "second")
            (root / "second").write_text(
                "Not a skill directory.\n", encoding="utf-8", newline="\n"
            )
            self.assertTrue(selection_problems(root, {"first", "second"}))

    def test_uninstall_rejects_redirected_sources_without_removal(self) -> None:
        for kind in ("catalog", "profile", "nested-skill-resource"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                parent = Path(directory)
                root, home = parent / "source", parent / "home"
                root.mkdir()
                home.mkdir()
                write_fixture(root)
                aa.write_rendered(root)
                aa.install_links(root, home)
                entries = aa.native_plan(root, home)
                if kind == "catalog":
                    original = root / "catalog.toml"
                elif kind == "profile":
                    asset = next(a for a in aa.load_catalog(root).assets if a.kind == "profile")
                    original = root / asset.path
                else:
                    original = root / "skills/route-subagents/SKILL.md"
                external = parent / "external-source"
                expected = original.read_bytes()
                external.write_bytes(expected)
                original.unlink()
                try:
                    original.symlink_to(external)
                except OSError as error:
                    self.skipTest(f"symlink unavailable: {error}")
                with self.assertRaisesRegex(aa.ContractError, "linked resource"):
                    aa.uninstall_links(root, home)
                self.assertTrue(all(aa.lexists(entry.target) for entry in entries))
                self.assertEqual(expected, external.read_bytes())


if __name__ == "__main__":
    unittest.main()
