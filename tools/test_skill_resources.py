from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.skill_resources import (
    distribution_problems, markdown_problems, markdown_targets, selection_problems,
)


def skill(root: Path, name: str, body: str = "", optional: str | None = None) -> Path:
    path = root / name
    path.mkdir(parents=True)
    metadata = "" if optional is None else f'metadata:\n  assay-optional-skills: "{optional}"\n'
    (path / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: A bounded method.\nlicense: MIT\n{metadata}---\n\n{body}\n",
        encoding="utf-8",
    )
    return path


class SkillResourceTests(unittest.TestCase):
    def test_commonmark_links_not_code_examples(self) -> None:
        text = '''[reference][id]

[id]: <file name.md> "title"

[balanced](a_(b).md)
<img src="image.png"/>
`[not a link](absent.md)`

```md
[example](also-absent.md)
```
'''
        self.assertEqual(
            {"file%20name.md", "a_(b).md", "image.png"}, set(markdown_targets(text))
        )

    def test_reference_links_are_validated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "source.md"
            path.write_text('[one][id]\n\n[id]: missing.md "A title"\n', encoding="utf-8")
            self.assertTrue(markdown_problems(path, root))
            (root / "missing.md").write_text("Present\n", encoding="utf-8")
            self.assertEqual([], markdown_problems(path, root))

    def test_declared_peer_can_be_absent_but_local_resource_cannot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = skill(root, "first", "[peer](../second/SKILL.md)\n[core](references/core.md)", "second")
            self.assertTrue(selection_problems(root, {"first", "second"}))
            (first / "references").mkdir()
            (first / "references/core.md").write_text("Required core.\n", encoding="utf-8")
            self.assertEqual([], selection_problems(root, {"first", "second"}))

    def test_undeclared_unknown_duplicate_self_and_unused_peers_fail(self) -> None:
        for declared in (None, "unknown", "second second", "first", "second unused"):
            with self.subTest(declared=declared), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                skill(root, "first", "[peer](../second/SKILL.md)", declared)
                self.assertTrue(selection_problems(root, {"first", "second", "unused"}))

    def test_optional_declaration_cannot_hide_broken_present_peer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = skill(root, "first", "[peer](../second/absent.md)", "second")
            second = skill(root, "second")
            self.assertTrue(distribution_problems([first, second]))
            (second / "absent.md").write_text("Real criterion.\n", encoding="utf-8")
            self.assertEqual([], distribution_problems([first, second]))

    def test_outside_and_encoded_traversal_fail(self) -> None:
        # These paths are hostile runtime inputs, not repository resources.
        # Construct them from path segments so source dependency inspection
        # does not mistake a deliberate escape fixture for a real dependency.
        filename = "outside.md"
        targets = (
            "/".join(("..", "..", filename)),
            "/".join(("%2e%2e", "%2e%2e", filename)),
            "/" + filename,
        )
        for target in targets:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "skills"
                root.mkdir()
                skill(root, "first", f"[outside]({target})")
                self.assertTrue(selection_problems(root, {"first"}))

    def test_empty_and_unknown_selection_do_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertTrue(selection_problems(root, {"known"}))
            skill(root, "unknown")
            self.assertTrue(selection_problems(root, {"known"}))
            self.assertTrue(distribution_problems([]))

    def test_links_are_rejected_before_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = skill(root, "first")
            external = root / "external.md"
            external.write_text("Must not follow.\n", encoding="utf-8")
            try:
                (first / "linked.md").symlink_to(external)
            except OSError as error:
                self.skipTest(f"symlink unavailable: {error}")
            self.assertTrue(distribution_problems([first]))
            self.assertTrue(selection_problems(root, {"first"}))


if __name__ == "__main__":
    unittest.main()
