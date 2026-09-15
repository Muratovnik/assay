"""Vendor guidance extraction: quoted sections, kept caveats, loud drift."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_benchmark_router import GUIDES, guide_data, request, view
from route_evidence.cache import Cache, contract
from route_evidence.core import EvidenceError, validate_guide
from route_evidence.guides import (EXTRACTOR_VERSION, MAX_EXCERPT, anchor, guide_ids,
                                   guide_snapshot, section_text)
from route_evidence.routing import brief, build_context

SOURCE = GUIDES["openai-reasoning"]
FIRST, SECOND = SOURCE["sections"]

PAGE = """---
title: Reasoning models
url: https://example.invalid/docs/reasoning
---

<Warning>This page applies to reasoning models only.</Warning>

Intro prose.

## {first}

Effort prose.

<Note>Unsupported on some models.</Note>

```python
# Reasoning effort
client.responses.create(effort="low")
```

### Subsection

Subsection prose.

## {second}

Cost prose.

## Unrelated section

Ignored prose.
""".format(first=FIRST, second=SECOND)


def page(**changes):
    body = PAGE
    for old, new in changes.items():
        body = body.replace(old.replace("_", " "), new)
    return body


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = guide_snapshot(SOURCE, PAGE)
        self.sections = {s["section"]: s for s in self.snapshot["retrieved_sections"]}

    def test_section_includes_subsections_and_stops_at_the_next_peer(self):
        effort = self.sections[FIRST]
        self.assertIn("Effort prose.", effort["excerpt"])
        self.assertIn("Subsection prose.", effort["excerpt"])
        self.assertNotIn("Cost prose.", effort["excerpt"])
        self.assertNotIn("Ignored prose.", effort["excerpt"])

    def test_heading_inside_a_code_fence_is_not_a_section(self):
        # Real vendor pages put "# ..." comments inside examples.
        self.assertIsNone(section_text(PAGE, "Reasoning effort\nclient.responses"))
        self.assertNotIn("client.responses.create", self.sections[FIRST]["excerpt"])
        self.assertEqual(self.sections[FIRST]["code_blocks_omitted"], 1)

    def test_missing_section_is_loud_drift_not_a_quiet_gap(self):
        moved = PAGE.replace("## " + FIRST, "## Renamed by the publisher")
        with self.assertRaises(EvidenceError) as caught:
            guide_snapshot(SOURCE, moved)
        self.assertIn("guide_section_missing", str(caught.exception))
        self.assertIn(FIRST, str(caught.exception))

    def test_section_caveats_are_kept_whole_and_out_of_the_prose(self):
        effort = self.sections[FIRST]
        self.assertEqual(effort["caveats"], [{"kind": "note", "text": "Unsupported on some models.",
                                              "truncated": False}])
        self.assertNotIn("Unsupported on some models.", effort["excerpt"])

    def test_page_level_caveats_survive_section_selection(self):
        self.assertEqual([c["text"] for c in self.snapshot["document_caveats"]],
                         ["This page applies to reasoning models only."])

    def test_shortening_trims_prose_only_and_says_so(self):
        long_page = PAGE.replace("Effort prose.", "\n\n".join(["word " * 40] * 30))
        section = guide_snapshot(SOURCE, long_page)["retrieved_sections"][0]
        self.assertTrue(section["truncated"])
        self.assertLessEqual(section["characters"], MAX_EXCERPT)
        self.assertTrue(section["excerpt"].endswith("word"))
        self.assertEqual(section["caveats"][0]["text"], "Unsupported on some models.")

    def test_provenance_is_anchored_to_the_publisher_page(self):
        effort = self.sections[FIRST]
        self.assertEqual(self.snapshot["canonical_url"], "https://example.invalid/docs/reasoning")
        self.assertEqual(effort["url"], "https://example.invalid/docs/reasoning#" + anchor(FIRST))
        self.assertEqual(self.snapshot["document_title"], "Reasoning models")
        self.assertEqual(self.snapshot["publisher"], "OpenAI")
        self.assertEqual(self.snapshot["extractor_version"], EXTRACTOR_VERSION)

    def test_derived_content_follows_the_source_bytes(self):
        other = guide_snapshot(SOURCE, PAGE.replace("Cost prose.", "Different cost prose."))
        self.assertNotEqual(other["content_hash"], self.snapshot["content_hash"])
        self.assertEqual(guide_snapshot(SOURCE, PAGE)["content_hash"], self.snapshot["content_hash"])

    def test_title_falls_back_to_the_first_heading_without_front_matter(self):
        plain = "# Reasoning models\n\n" + PAGE[PAGE.index("<Warning>"):]
        self.assertEqual(guide_snapshot(SOURCE, plain)["document_title"], "Reasoning models")

    def test_untitled_document_is_refused(self):
        with self.assertRaises(EvidenceError):
            guide_snapshot(SOURCE, PAGE[PAGE.index("<Warning>"):])

    def test_extractor_version_mismatch_is_refused(self):
        with self.assertRaises(EvidenceError):
            guide_snapshot({**SOURCE, "extractor_version": EXTRACTOR_VERSION + 1}, PAGE)


class ContractTests(unittest.TestCase):
    def test_guide_registry_binds_publisher_client_and_https(self):
        for gid, source in GUIDES.items():
            with self.subTest(guide=gid):
                self.assertTrue(source["url"].startswith("https://"))
                self.assertEqual(source["kind"], "guide")
                self.assertTrue(source["clients"])
                self.assertTrue(source["sections"])
        self.assertEqual(guide_ids("codex"), ["openai-reasoning"])
        self.assertEqual(guide_ids("claude"), ["claude-model-choice", "claude-thinking"])
        self.assertEqual(guide_ids("unconfigured"), [])

    def test_validate_guide_rejects_insecure_or_empty_documents(self):
        good = guide_data()
        validate_guide(good)
        for change in ({"canonical_url": "http://example.invalid/x"}, {"retrieved_sections": []},
                       {"applies_to": []}, {"extractor_version": 0}, {"document_caveats": "none"}):
            with self.subTest(change=str(change)[:60]), self.assertRaises(EvidenceError):
                validate_guide({**good, **change})

    def test_cache_keeps_guide_identity_separate_from_benchmarks(self):
        validate, identity = contract(SOURCE)
        self.assertEqual(validate, validate_guide)
        self.assertIn(("extractor_version", "extractor_version"), identity)
        with tempfile.TemporaryDirectory() as tmp:
            cache = Cache(Path(tmp))
            stored = cache.get(SOURCE, lambda source, validators: (guide_data(), {}))
            self.assertEqual(stored["refresh"], "updated")
            self.assertEqual(stored["kind"], "guide")
            # A new extractor invalidates the derived cache, as a new source
            # revision would: the stored excerpt was produced by the old rules.
            upgraded = {**SOURCE, "extractor_version": EXTRACTOR_VERSION + 1}
            self.assertIsNone(cache.read(upgraded).get("snapshot"))

    def test_guidance_never_becomes_a_measurement(self):
        result = build_context(request(), [view()], guidance=[
            {"source_id": "openai-reasoning", "source_url": SOURCE["url"], "kind": "guide",
             "stale": False, "last_success_at": "2026-09-14T06:00:00Z", "snapshot": guide_data()}])
        self.assertEqual(result["guidance"]["documents"][0]["publisher"], "OpenAI")
        self.assertNotIn("openai-reasoning", [c["source_id"] for c in result["tasks"][0]["primary_comparisons"]])
        for candidate in result["tasks"][0]["primary_comparisons"][0]["candidates"]:
            self.assertNotIn("guide", candidate["expenses"])
        self.assertIn("not an instruction", result["guidance"]["note"])

    def test_brief_keeps_the_whole_guidance_block(self):
        result = build_context(request(), [view()], guidance=[
            {"source_id": "openai-reasoning", "source_url": SOURCE["url"], "kind": "guide",
             "stale": False, "last_success_at": None, "snapshot": guide_data()}])
        self.assertEqual(brief(result)["guidance"], result["guidance"])


if __name__ == "__main__":
    unittest.main()
