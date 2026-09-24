"""Deterministic diagnostic contracts, not model-quality or discovery evidence."""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "revision_check.py"
SPEC = importlib.util.spec_from_file_location("revision_check", SCRIPT)
assert SPEC and SPEC.loader
rc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rc)


def changes(before: str, after: str, sources: list[str] | None = None) -> set[tuple[str, str, str]]:
    report = rc.analyze(before, after, sources=sources)
    return {(item["direction"], item["kind"], item["value"]) for item in report["facts"]["changes"]}


def long_text() -> str:
    return "\n\n".join(["This paragraph describes a documented operation and explains the required context clearly. " * 4] * 3)


class FactTests(unittest.TestCase):
    def test_number_substring_is_not_evidence(self):
        self.assertIn(("added", "number", "10"), changes("There are 100 users.", "There are 10 users."))

    def test_numeric_boundaries(self):
        self.assertEqual(rc.extract("abc100 100abc", "before"), [])

    def test_unit_change(self):
        self.assertEqual(changes("Wait 10 ms.", "Wait 10 s."),
                         {("removed", "quantity", "10 ms"), ("added", "quantity", "10 s")})

    def test_unit_case_is_not_folded(self):
        self.assertTrue(changes("Size: 10 MB.", "Size: 10 mb."))

    def test_grouping_whitespace(self):
        for separator in (" ", "\u00a0", "\u202f"):
            with self.subTest(separator=repr(separator)):
                self.assertFalse(changes("Size: 1000 mg.", f"Size: 1{separator}000 mg."))

    def test_decimal_comma(self):
        self.assertIn(("added", "quantity", "1,5 мг"), changes("Доза: 1 мг.", "Доза: 1,5 мг."))

    def test_signed_number(self):
        self.assertIn(("added", "number", "-10"), changes("Value: 10.", "Value: -10."))

    def test_unicode_minus(self):
        self.assertFalse(changes("Value: -10.", "Value: −10."))

    def test_scientific_notation(self):
        self.assertIn(("added", "number", "1e-3"), changes("Value: 1e-2.", "Value: 1e-3."))

    def test_currency_forms(self):
        self.assertFalse(changes("Price: $10.", "Price: 10 $."))

    def test_percent(self):
        self.assertIn(("added", "quantity", "5 %"), changes("Growth: 10%.", "Growth: 5%."))

    def test_date_consumes_internal_numbers(self):
        found = rc.extract("Due 2026-09-25.", "before")
        self.assertEqual([(x["kind"], x["key"]) for x in found], [("date", "2026-09-25")])

    def test_numeric_russian_date(self):
        self.assertIn(("added", "date", "26.09.2026"), changes("Срок: 25.09.2026.", "Срок: 26.09.2026."))

    def test_versions(self):
        self.assertEqual([(x["kind"], x["key"]) for x in rc.extract("Use v1.2 or 2.1.3-beta.", "before")],
                         [("version", "v1.2"), ("version", "2.1.3-beta")])

    def test_url_is_atomic(self):
        found = rc.extract("See https://example.invalid/v100?limit=10.", "before")
        self.assertEqual([x["kind"] for x in found], ["url"])
        self.assertEqual(found[0]["key"], "https://example.invalid/v100?limit=10")

    def test_balanced_markdown_url(self):
        found = rc.extract("[Link](https://example.invalid/a_(b))", "before")
        self.assertEqual(found[0]["key"], "https://example.invalid/a_(b)")

    def test_line_column(self):
        found = rc.extract("Heading\nWait 10 ms.", "before")
        self.assertEqual((found[0]["line"], found[0]["column"]), (2, 6))

    def test_multiple_sources_record_provenance(self):
        result = rc.analyze("Count: 10.", "Count: 10; limit: 20.", sources=["Version v2.1.", "Limit: 20."])
        self.assertFalse(result["facts"]["changes"])
        supported = result["facts"]["source_backed_additions"]
        self.assertEqual(supported[0]["source_matches"][0]["source"], "source[2]")

    def test_unused_notes_do_not_become_required_content(self):
        self.assertFalse(changes("Count: 10.", "Count: 10.", ["Additional background: 20."]))

    def test_removal_remains_visible_when_in_notes(self):
        self.assertIn(("removed", "number", "10"), changes("Count: 10.", "Count unspecified.", ["Count: 10."]))

    def test_repeated_mentions_do_not_invent_a_fact_change(self):
        self.assertFalse(changes("10 users. All 10 users agreed.", "10 users agreed."))

    def test_equal_inventory_is_not_semantic_proof(self):
        result = rc.analyze("May retry after 10 seconds.", "Must retry after 10 seconds.")
        self.assertEqual(result["facts"]["status"], "observed")
        self.assertIn("modality", result["facts"]["limits"])
        self.assertEqual(set(result["claims"].values()), {"unverified"})

    def test_empty_inputs(self):
        for before, after, sources in [("", "Text", []), ("Text", " ", []), ("Text", "Text", [""])]:
            with self.subTest(before=before, after=after, sources=sources), self.assertRaises(ValueError):
                rc.analyze(before, after, sources=sources)

    def test_nul_rejected(self):
        with self.assertRaises(ValueError):
            rc.analyze("Text\x00", "Text")

    def test_inspecting_no_fact_is_unverified(self):
        report = rc.analyze("Plain text.", "Still plain text.")
        self.assertEqual(rc.exit_code(report, False), 2)

    def test_diagnostic_and_strict_exit_contract(self):
        report = rc.analyze("10 users.", "20 users.")
        self.assertEqual((rc.exit_code(report, False), rc.exit_code(report, True)), (0, 1))

    def test_same_known_facts_complete_without_success_claim(self):
        report = rc.analyze("10 users.", "10 users.")
        self.assertEqual((report["status"], rc.exit_code(report, True)), ("observed", 0))

    def test_hashes_identify_inputs(self):
        report = rc.analyze("10 users.", "20 users.")
        self.assertEqual(report["input_text_sha256"]["before"], hashlib.sha256(b"10 users.").hexdigest())


class StyleTests(unittest.TestCase):
    def test_opt_in_only(self):
        self.assertEqual(rc.analyze("10 users.", "10 users.")["style"], {"status": "not-requested"})

    def test_long_prose_without_facts_can_be_observed(self):
        report = rc.analyze(long_text(), long_text(), style=True, language="en")
        self.assertEqual(report["status"], "observed")
        self.assertEqual(set(report["style"]["delta"].values()), {0})

    def test_russian_segmentation(self):
        text = "Это предложение описывает порядок работы и сохраняет исходные условия задачи. " * 15
        self.assertEqual(rc.style_metrics(text, "ru", 100)["status"], "observed")

    def test_unsupported_language_never_passes(self):
        for language in ("unknown", "de", "zh"):
            with self.subTest(language=language):
                report = rc.analyze("10 " + long_text(), "20 " + long_text(), style=True, language=language)
                self.assertTrue(report["facts"]["changes"])
                self.assertEqual(rc.exit_code(report, True), 2)

    def test_short_text_is_unverified_not_normalized(self):
        report = rc.analyze("10 users.", "20 users.", style=True, language="en")
        self.assertEqual(report["style"]["status"], "unverified")
        self.assertEqual(rc.exit_code(report, False), 2)

    def test_code_frontmatter_and_inline_code_excluded(self):
        body, headings, items = rc.prose("---\ntitle: internal\n---\n# Heading\n\nUse `secret`.\n```py\nprint(10)\n```\n- Next step")
        self.assertNotIn("secret", body)
        self.assertNotIn("print", body)
        self.assertNotIn("internal", body)
        self.assertEqual((headings, items), (1, 1))

    def test_unclosed_markup_unverified(self):
        for text in ("```\n" + long_text(), "---\ntitle: unfinished\n" + long_text()):
            with self.subTest(text=text[:10]):
                self.assertEqual(rc.style_metrics(text, "en", 100)["status"], "unverified")

    def test_fence_marker_inside_code_is_not_a_closer(self):
        body, _, _ = rc.prose("````py\n```\nsecret\n````\nVisible.")
        self.assertNotIn("secret", body)
        self.assertIn("Visible", body)

    def test_html_table_indented_code_unverified(self):
        for prefix in ("<p>text</p>\n", "| One | Two |\n", "    code\n"):
            with self.subTest(prefix=prefix):
                self.assertEqual(rc.style_metrics(prefix + long_text(), "en", 100)["status"], "unverified")

    def test_fragmentation_is_a_question_not_a_failure(self):
        before = "One useful explanation joins several facts and preserves their relationships. " * 15
        after = "One fact. Another fact. Next fact. More context. " * 15
        report = rc.analyze(before, after, style=True, language="en")
        self.assertTrue(report["style"]["review_questions"])
        self.assertEqual(rc.exit_code(report, True), 0)
        self.assertEqual(report["style"]["calibration"], "none; no quality or authorship inference")

    def test_heading_loss_is_not_automatically_wrong(self):
        report = rc.analyze("# Overview\n\n" + long_text(), long_text(), style=True, language="en")
        self.assertEqual(report["style"]["delta"]["headings"], -1)
        self.assertEqual(rc.exit_code(report, True), 0)

    def test_supplied_terms_are_literal_and_not_blacklisted(self):
        report = rc.analyze("C++ stays. " + long_text(), "Other language. " + long_text(),
                            style=True, language="en", terms=["C++"])
        self.assertEqual(report["style"]["term_counts"], [{"term": "C++", "before": 1, "after": 0}])
        self.assertTrue(any("supplied term" in q for q in report["style"]["review_questions"]))

    def test_terms_without_style_are_not_silently_ignored(self):
        with self.assertRaises(ValueError):
            rc.analyze("10 users.", "10 users.", terms=["users"])

    def test_invalid_minimum_and_empty_term(self):
        for kwargs in ({"minimum": 0}, {"terms": [" "]}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                rc.analyze("10 users.", "10 users.", **kwargs)


class FixtureTests(unittest.TestCase):
    def test_revision_pairs_have_separate_inputs_and_grading(self):
        skills = SCRIPT.parents[2]
        for name, expected_count in (("text-writing", 6), ("technical-writing", 4)):
            with self.subTest(skill=name):
                directory = skills / name / "evals"
                inputs = json.loads((directory / "revision-cases.json").read_text(encoding="utf-8"))
                rubric = json.loads((directory / "revision-rubric.json").read_text(encoding="utf-8"))
                self.assertEqual(inputs["schema_version"], 1)
                self.assertEqual(inputs["skill_name"], name)
                self.assertEqual(rubric["skill_name"], name)
                ids = [case["id"] for case in inputs["cases"]]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertEqual(len(ids), expected_count)
                self.assertEqual(set(ids), {case["id"] for case in rubric["cases"]})
                for case in inputs["cases"]:
                    self.assertLessEqual(set(case), {"id", "prompt", "context", "files"})
                    self.assertTrue(case["prompt"].strip())
                self.assertNotIn("style_score", rubric["dimensions"])


class CLITests(unittest.TestCase):
    def invoke(self, before: bytes, after: bytes, *flags: str, environment: dict[str, str] | None = None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = [root / "before.md", root / "after.md"]
            for path, data in zip(paths, (before, after)):
                path.write_bytes(data)
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), *map(str, paths), *flags],
                                    capture_output=True, encoding="utf-8", check=False, env=environment)
            self.assertEqual([path.read_bytes() for path in paths], [before, after])
            self.assertEqual(set(root.iterdir()), set(paths))
            self.assertFalse(result.stderr)
            return result

    def test_json_and_text_share_status_and_exit(self):
        for strict in ([], ["--strict"]):
            data = self.invoke(b"10 users.", b"20 users.", "--json", *strict)
            text = self.invoke(b"10 users.", b"20 users.", *strict)
            self.assertEqual(data.returncode, text.returncode)
            self.assertIn(json.loads(data.stdout)["status"], text.stdout.splitlines()[0])
            self.assertIn("added number", text.stdout)

    def test_unicode_input_json(self):
        result = self.invoke("Доза 1 мг.".encode(), "Доза 2 мг.".encode(), "--json", "--strict")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "review")

    def test_cli_utf8_is_independent_of_legacy_pipe_encoding(self):
        for encoding in ("ascii", "cp1252"):
            for flags in (["--json"], []):
                with self.subTest(encoding=encoding, flags=flags):
                    result = self.invoke("Доза 1 мг.".encode(), "Доза 2 мг.".encode(),
                                         "--strict", *flags,
                                         environment=dict(os.environ, PYTHONIOENCODING=encoding))
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("мг", result.stdout)
                    if flags:
                        self.assertEqual(json.loads(result.stdout)["status"], "review")

    def test_invalid_utf8_is_machine_readable(self):
        result = self.invoke(b"\xff", b"10 users.", "--json")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "unverified")

    def test_empty_file_is_machine_readable(self):
        result = self.invoke(b"", b"10 users.", "--json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", json.loads(result.stdout))

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(rc.main([str(Path(temporary) / "missing"), str(Path(temporary) / "also-missing"), "--json"]), 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "unverified")

    def test_input_size_guard(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "large"
            path.write_bytes(b"a" * (rc.MAX_BYTES + 1))
            with self.assertRaises(ValueError):
                rc.read_text(path)

    def test_requested_unsupported_style_has_json_text_parity(self):
        for flags in (["--json"], []):
            result = self.invoke(b"10 users.", b"10 users.", "--style", "--language", "de", *flags)
            self.assertEqual(result.returncode, 2)
            self.assertIn("unverified", result.stdout)


if __name__ == "__main__":
    unittest.main()
