from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from tools import assay as aa
from tools.asset_formats import yaml_mapping
from tools.test_assay import write_fixture


class MetadataFormatTests(unittest.TestCase):
    def parse(self, body: str) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "SKILL.md"
            path.write_text(f"---\n{body}\n---\n\n# Method\n", encoding="utf-8")
            return aa.frontmatter(path)

    def test_standard_scalar_forms(self) -> None:
        examples = {
            'description: "Audit: tests"': "Audit: tests",
            "description: >\n  Audit tests\n  against requirements.": "Audit tests against requirements.\n",
            "description: |\n  Audit tests\n  against requirements.": "Audit tests\nagainst requirements.\n",
            "description: 'It''s a method'": "It's a method",
            "description: Inspect code # a YAML comment": "Inspect code",
        }
        for body, expected in examples.items():
            with self.subTest(body=body):
                self.assertEqual(expected, self.parse(body)["description"])

    def test_invalid_yaml_and_ambiguous_keys_are_rejected(self) -> None:
        for body in (
            "description: Audit: tests",
            "name: first\nname: second",
            "metadata:\n  author: first\n  author: second",
            "description: &value Audit\nlicense: *value",
            "metadata: {1: value}",
            "[one, two]",
            "description: [unterminated",
            "description: !!python/object:builtins.object {}",
        ):
            with self.subTest(body=body), self.assertRaises(aa.ContractError):
                self.parse(body)

    def test_policy_booleans_and_global_loader_are_unchanged(self) -> None:
        import yaml
        self.assertEqual({"yes": "on", "enabled": True}, yaml_mapping("yes: on\nenabled: true", label="fixture"))
        self.assertEqual({True: True}, yaml.safe_load("yes: on"))
        self.assertEqual({"policy": {"allow_implicit_invocation": False}}, aa.openai_adapter_document("policy:\n  allow_implicit_invocation: false\n"))

    def test_catalog_validation_checks_field_types_and_lengths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            asset = aa.load_catalog(root).assets[0]
            path = root / asset.path / "SKILL.md"
            base = "name: route-subagents\nlicense: MIT\n"
            invalid = (
                "description: true", "description: null", "description: []",
                'description: "' + "x" * 1025 + '"',
                "description: Valid\ncompatibility: 42",
                'description: Valid\ncompatibility: "' + "x" * 501 + '"',
                "description: Valid\nmetadata: {revision: 2}",
                "description: Valid\nallowed-tools: [Read]",
            )
            for extra in invalid:
                with self.subTest(extra=extra[:80]):
                    path.write_text(f"---\n{base}{extra}\n---\n", encoding="utf-8")
                    self.assertTrue(aa.skill_problems(path, asset, root))
            path.write_text(f'---\n{base}description: >\n  Inspect code\n  against a contract.\nmetadata:\n  revision: "2"\n---\n', encoding="utf-8")
            self.assertEqual([], aa.skill_problems(path, asset, root))


class UninstallBoundaryTests(unittest.TestCase):
    def test_uninstall_does_not_require_publication_cleanliness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, home = Path(directory) / "source", Path(directory) / "home"
            root.mkdir()
            home.mkdir()
            write_fixture(root)
            aa.write_rendered(root)
            aa.install_links(root, home)
            (root / "README.md").write_bytes(b"Incomplete editing state")
            self.assertTrue(aa.check(root))
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result = aa.main(["--root", str(root), "uninstall-links", "--home", str(home)])
            self.assertEqual(0, result)
            self.assertTrue(all(aa.entry_state(entry)[0] == "missing" for entry in aa.native_plan(root, home)))

    def test_modified_adapter_still_prevents_all_removal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, home = Path(directory) / "source", Path(directory) / "home"
            root.mkdir()
            home.mkdir()
            write_fixture(root)
            aa.write_rendered(root)
            aa.install_links(root, home)
            entries = aa.native_plan(root, home)
            adapter = next(entry for entry in entries if entry.mode == "render")
            adapter.target.write_bytes(b"user-owned edit\n")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                result = aa.main(["--root", str(root), "uninstall-links", "--home", str(home)])
            self.assertEqual(1, result)
            self.assertEqual(b"user-owned edit\n", adapter.target.read_bytes())
            self.assertTrue(all(aa.lexists(entry.target) for entry in entries))


if __name__ == "__main__":
    unittest.main()
