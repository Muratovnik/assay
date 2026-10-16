from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.skill_resources import (
    distribution_problems, markdown_problems, markdown_targets, selection_problems,
    unreachable_problems,
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

    def test_section_anchors_are_validated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "target.md").write_text(
                "# Target\n\n## Report the `Reuse` decision\n\n## Notes\n\n## Notes\n\n"
                "## Условия проекта\n", encoding="utf-8")
            path = root / "source.md"
            for link in ("target.md#report-the-reuse-decision", "target.md#notes-1",
                         "target.md#%D1%83%D1%81%D0%BB%D0%BE%D0%B2%D0%B8%D1%8F-%D0%BF%D1%80%D0%BE%D0%B5%D0%BA%D1%82%D0%B0",
                         "#local-part"):
                with self.subTest(link=link):
                    path.write_text(f"# Source\n\n## Local part\n\n[ok]({link})\n", encoding="utf-8")
                    self.assertEqual([], markdown_problems(path, root))
            for link in ("target.md#missing-part", "target.md#notes-2", "#absent"):
                with self.subTest(link=link):
                    path.write_text(f"# Source\n\n[bad]({link})\n", encoding="utf-8")
                    self.assertTrue(markdown_problems(path, root))

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



class ReachabilityTests(unittest.TestCase):
    """Every file under references/ and examples/ must be linked from SKILL.md, directly or transitively."""

    def fixture(self, directory: str) -> tuple[Path, Path]:
        root = Path(directory)
        first = skill(root, "first", "[core](references/core.md)")
        (first / "references").mkdir()
        (first / "examples").mkdir()
        (first / "references/core.md").write_text(
            "Core. Read [the deep case](deep.md) when X.\n", encoding="utf-8")
        (first / "references/deep.md").write_text(
            "Deep. See [a sample](../examples/sample.md).\n", encoding="utf-8")
        (first / "examples/sample.md").write_text("Sample.\n", encoding="utf-8")
        return root, first

    def test_complete_skill_passes_including_files_reached_only_through_another_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, first = self.fixture(directory)
            self.assertEqual([], unreachable_problems(first, root))

    def test_an_unlinked_reference_fails_naming_the_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, first = self.fixture(directory)
            (first / "references/orphan.md").write_text("Nobody links this.\n", encoding="utf-8")
            (first / "examples/loose.json").write_text("{}\n", encoding="utf-8")
            problems = unreachable_problems(first, root)
            self.assertEqual(2, len(problems), problems)
            self.assertEqual(
                ["first/examples/loose.json", "first/references/orphan.md"],
                sorted(problem.split(": ")[0] for problem in problems),
            )
            self.assertTrue(all(": not reachable" in problem for problem in problems), problems)

    def test_a_link_from_evals_or_a_code_example_or_another_skill_does_not_reach(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, first = self.fixture(directory)
            (first / "references/orphan.md").write_text("Nobody links this.\n", encoding="utf-8")
            (first / "evals").mkdir()
            (first / "evals/case.md").write_text("[graded](../references/orphan.md)\n", encoding="utf-8")
            skill(root, "second", "[elsewhere](../first/references/orphan.md)\n\n"
                  "`[code](references/orphan.md)`\n\n```md\n[fenced](references/orphan.md)\n```\n")
            self.assertEqual(
                ["first/references/orphan.md"],
                [problem.split(": ")[0] for problem in unreachable_problems(first, root)],
            )

    def test_a_link_chain_that_never_starts_at_skill_md_does_not_reach(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root, first = self.fixture(directory)
            (first / "references/a.md").write_text("[b](b.md)\n", encoding="utf-8")
            (first / "references/b.md").write_text("[a](a.md)\n", encoding="utf-8")
            self.assertEqual(
                ["first/references/a.md", "first/references/b.md"],
                [problem.split(": ")[0] for problem in unreachable_problems(first, root)],
            )


if __name__ == "__main__":
    unittest.main()
