"""Publisher caveats keep their conditions; quoted examples are not advice."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "route-subagents" / "scripts"))

from route_evidence.core import EvidenceError
from route_evidence.guides import GUIDES, guide_snapshot


class GuideCaveatTests(unittest.TestCase):
    def guide(self, content, *, preamble=""):
        source = GUIDES["openai-reasoning"]
        first, second = source["sections"]
        return guide_snapshot(source, f"# Example\n\n{preamble}\n\n## {first}\n\n{content}\n\n## {second}\n\nCosts.")

    def test_real_callout_keeps_fenced_condition_and_quoted_closing_tag(self):
        condition = ('Use this setting only when the configuration is:\n\n'
                     '```json\n{"thinking": "adaptive", "example": "</Warning>"}\n```\n\n'
                     'The required tool permission must also be present.')
        section = self.guide(f"<Warning>{condition}</Warning>\n\n<Note>Actual condition.</Note>")["retrieved_sections"][0]
        self.assertEqual(section["caveats"], [
            {"kind": "warning", "text": condition, "truncated": False},
            {"kind": "note", "text": "Actual condition.", "truncated": False}])
        self.assertEqual(section["code_blocks_omitted"], 0)

    def test_whole_callout_size_limit_includes_its_code(self):
        content = "<Warning>Required configuration:\n\n```text\n" + "x" * 800 + "\n```\n</Warning>"
        with self.assertRaisesRegex(EvidenceError, "guide_caveat_size_limit_exceeded"):
            self.guide(content)

    def test_fenced_examples_in_containers_are_not_publisher_caveats(self):
        examples = (
            "```xml\n<Warning>Quoted example.</Warning>\n```",
            "1. Example:\n\n    ```xml\n    <Warning>Quoted example.</Warning>\n    ```",
            "> ```xml\n> <Warning>Quoted example.</Warning>\n> ```",
            "> - ```xml\n>   <Warning>Quoted example.</Warning>\n>   ```",
            "    <Warning>Quoted example.</Warning>",
            "    - <Warning>Quoted example.</Warning>",
        )
        for example in examples:
            with self.subTest(example=example):
                section = self.guide(example + "\n\n<Note>Actual condition.</Note>")["retrieved_sections"][0]
                self.assertEqual(section["caveats"], [{"kind": "note", "text": "Actual condition.", "truncated": False}])
                self.assertNotIn("Quoted example", section["excerpt"])
                self.assertEqual(section["code_blocks_omitted"], 1)

    def test_actual_caveats_in_list_quote_and_continued_paragraph_remain(self):
        examples = (
            "1. Scope:\n\n    <Note>Actual condition.</Note>",
            "> <Note>Actual condition.</Note>",
            "The following condition applies:\n    <Note>Actual condition.</Note>",
        )
        for example in examples:
            with self.subTest(example=example):
                section = self.guide(example)["retrieved_sections"][0]
                self.assertEqual(section["caveats"], [{"kind": "note", "text": "Actual condition.", "truncated": False}])

    def test_indented_literal_closer_does_not_end_top_level_fence(self):
        example = "```xml\n    ```\n<Warning>Quoted example.</Warning>\n```"
        section = self.guide(example + "\n\n<Note>Actual condition.</Note>")["retrieved_sections"][0]
        self.assertEqual(section["caveats"], [{"kind": "note", "text": "Actual condition.", "truncated": False}])
        self.assertNotIn("Quoted example", section["excerpt"])

    def test_inline_code_comments_and_escapes_are_not_publisher_caveats(self):
        examples = (
            "Use `<Warning>Quoted inline.</Warning>` as an example.",
            "Use ``<Warning>Quoted ` inline.</Warning>`` as an example.",
            "<!-- <Warning>Commented out.</Warning> -->",
            r"\<Warning>Escaped text.\</Warning>",
        )
        for example in examples:
            with self.subTest(example=example):
                section = self.guide(example + "\n\n<Warning>Actual warning.</Warning>")["retrieved_sections"][0]
                self.assertEqual(section["caveats"], [{"kind": "warning", "text": "Actual warning.", "truncated": False}])
                self.assertNotIn("Commented out", section["excerpt"])

    def test_real_callout_keeps_inline_code_and_escaped_tags(self):
        condition = r"Use `</Warning>` and `<Note>this literal</Note>` and \<Warning>escaped markup\</Warning> only."
        section = self.guide(f"<Warning>{condition}</Warning>")["retrieved_sections"][0]
        self.assertEqual(section["caveats"], [{"kind": "warning", "text": condition, "truncated": False}])

    def test_comment_delimiters_in_inline_code_do_not_hide_real_caveats(self):
        example = "The token `<!--` is quoted.\n\n<Note>Actual condition.</Note>"
        section = self.guide(example)["retrieved_sections"][0]
        self.assertEqual(section["caveats"], [{"kind": "note", "text": "Actual condition.", "truncated": False}])

    def test_page_callout_keeps_fenced_conditions_and_skips_quoted_examples(self):
        condition = 'Applies only to:\n\n```text\nreviewed-model\n```\n\nOther models are unsupported.'
        preamble = f"```xml\n<Warning>Quoted example.</Warning>\n```\n\n<Warning>{condition}</Warning>"
        guide = self.guide("Ordinary effort guidance.", preamble=preamble)
        self.assertEqual(guide["document_caveats"], [{"kind": "warning", "text": condition, "truncated": False}])
        self.assertEqual(guide["retrieved_sections"][0]["excerpt"], "Ordinary effort guidance.")


if __name__ == "__main__":
    unittest.main()
