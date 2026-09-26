"""Publication checks for the flow-mapping method; not agent behavior tests."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools import assay as aa
from tools import eval_assets as ea

ROOT = Path(__file__).resolve().parents[1]
NAME = "product-flow-mapping"
SKILL = ROOT / "skills" / NAME


class ProductFlowMethodTests(unittest.TestCase):
    def test_catalog_and_native_projection(self) -> None:
        catalog = aa.load_catalog(ROOT)
        matches = [item for item in catalog.assets if item.id == f"skill/{NAME}"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].activation, "automatic")
        self.assertEqual(matches[0].path, f"skills/{NAME}")
        with tempfile.TemporaryDirectory(prefix="assay-flow-projection-") as directory:
            home = Path(directory)
            entries = [entry for entry in aa.native_plan(ROOT, home)
                       if entry.asset_id == f"skill/{NAME}"]
            self.assertEqual({(entry.client, entry.source, entry.target, entry.mode)
                              for entry in entries}, {
                ("codex", SKILL, home / ".agents/skills" / NAME, "link"),
                ("claude", home / ".agents/skills" / NAME,
                 home / ".claude/skills" / NAME, "link"),
            })

    def test_corpora_use_the_existing_checker(self) -> None:
        self.assertEqual(ea.PAIRED_SKILLS.count(NAME), 1)
        for source, rubric in (("cases.json", "rubric.json"),
                               ("transfer-cases.json", "transfer-rubric.json")):
            with self.subTest(source=source):
                ea.check_pair(SKILL / "evals" / source, SKILL / "evals" / rubric, NAME)
        cases = ea.load(SKILL / "evals/cases.json")
        self.assertEqual({case["id"] for case in cases["cases"]},
                         {f"C{number:02}" for number in range(1, 21)})
        self.assertEqual({case["id"] for case in cases["discovery_cases"]},
                         {f"D{number:02}" for number in range(1, 9)})

    def test_existing_consumers_keep_the_method_link(self) -> None:
        # Link presence is publication wiring, not proof of a successful handoff.
        for name in ("operations-ui-delivery", "test-writing"):
            with self.subTest(consumer=name):
                source = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("../product-flow-mapping/SKILL.md", source)

    def test_retired_export_system_is_not_packaged(self) -> None:
        # Protect the requested removal without forbidding normal use of tools
        # or requiring a replacement implementation just to keep a test count.
        retired = (
            SKILL / "scripts/flow_map.py",
            SKILL / "scripts/requirements.txt",
            SKILL / "references/portable-map.md",
            SKILL / "examples/source-only-map.json",
            SKILL / "examples/notes.json",
            SKILL / "evals/browser/export.test.mjs",
            ROOT / "tools/test_product_flow_review.py",
        )
        for path in retired:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
