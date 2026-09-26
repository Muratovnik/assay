"""Flow-mapping corpus registration and consumer routes; no model grading.

Pair and schema validation belong to the evaluation-data gate and native links
to the compatibility fixture.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

from tools import eval_assets as ea

ROOT = Path(__file__).resolve().parents[1]
NAME = "product-flow-mapping"
SKILL = ROOT / "skills" / NAME
CONSUMERS = (
    "skills/operations-ui-delivery/SKILL.md",
    "skills/operations-ui-delivery/references/design-transfer.md",
    "skills/operations-ui-delivery/references/scenario-testing.md",
    "skills/test-writing/SKILL.md",
)


class ProductFlowMethodTests(unittest.TestCase):
    def test_registered_in_existing_checker(self) -> None:
        # The gate checks only registered corpora; dropping the name would pass silently.
        self.assertEqual(ea.PAIRED_SKILLS.count(NAME), 1)

    def test_consumers_route_to_the_inventory_owner(self) -> None:
        # Link presence is publication wiring, not proof of a successful handoff.
        for relative in CONSUMERS:
            with self.subTest(consumer=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("product-flow-mapping/SKILL.md", text)

    def test_runtime_links_resolve_outside_evaluation_data(self) -> None:
        for path in [SKILL / "SKILL.md", *(SKILL / "references").glob("*.md")]:
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if target.startswith(("https://", "http://", "#")):
                    continue
                linked = (path.parent / target.split("#", 1)[0]).resolve()
                with self.subTest(source=path.name, target=target):
                    self.assertTrue(linked.is_file())
                    self.assertNotIn("evals", linked.relative_to(ROOT.resolve()).parts)


if __name__ == "__main__":
    unittest.main()
