"""Tests for check --all: a gate's line is written when the gate ends, and test suites are counted."""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

from tools import check

ROOT = Path(__file__).resolve().parents[1]

SUITE = textwrap.dedent("""\
    import unittest

    class Sample(unittest.TestCase):
        def test_one(self):
            self.assertTrue(True)

        def test_two(self):
            self.assertTrue(True)

        @unittest.skip("fixture")
        def test_three(self):
            pass
""")


class CheckAll(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def run_gates(self, gates):
        output = io.StringIO()
        with mock.patch.object(check, "GATES", gates), \
                mock.patch.object(check, "SCRATCH", self.directory / "scratch"), \
                redirect_stdout(output):
            code = check.run_all()
        return code, output.getvalue()

    def suite(self, name, source):
        directory = self.directory / name
        directory.mkdir()
        if source:
            (directory / "test_sample.py").write_text(source, "utf-8")
        return ("-m", "unittest", "discover", "-s", str(directory), "-p", "test_*.py")

    def test_a_gate_line_reaches_redirected_output_before_the_next_gate_starts(self):
        # Output to a file is block-buffered unless the line is flushed, so the
        # second gate reads the file the first gate's line should already be in.
        log = self.directory / "check.log"
        probe = ("import os, sys; text = open(os.environ['CHECK_LOG'], encoding='utf-8').read(); "
                 "sys.exit(0 if text.startswith('first') else 1)")
        driver = textwrap.dedent(f"""\
            import sys
            from pathlib import Path
            sys.path[:0] = [{str(ROOT)!r}, {str(ROOT / "tools")!r}]
            from tools import check
            check.SCRATCH = Path({str(self.directory / "scratch")!r})
            check.GATES = (("first", ("-c", "pass")), ("second", ("-c", {probe!r})))
            raise SystemExit(check.run_all())
        """)
        with log.open("w", encoding="utf-8") as stream:
            completed = subprocess.run([sys.executable, "-B", "-c", driver], stdout=stream,
                                       stderr=subprocess.PIPE, text=True, check=False,
                                       env=dict(os.environ, CHECK_LOG=str(log)))
        lines = log.read_text("utf-8").splitlines()
        self.assertEqual(0, completed.returncode, (lines, completed.stderr))
        self.assertRegex(lines[0], r"^first\s+PASS$")
        self.assertRegex(lines[1], r"^second\s+PASS$")
        self.assertEqual("check --all: PASS", lines[-1])

    def test_a_test_suite_line_names_how_many_tests_ran_and_were_skipped(self):
        code, output = self.run_gates((("unit suite", self.suite("passing", SUITE)),))
        self.assertEqual(0, code, output)
        self.assertRegex(output, re.compile(r"^unit suite\s+PASS \(3 tests, 1 skipped\)$", re.MULTILINE))
        self.assertTrue(output.endswith("check --all: PASS\n"), output)

    def test_a_suite_that_ran_no_tests_fails(self):
        code, output = self.run_gates((("unit suite", self.suite("empty", "")),))
        self.assertEqual(1, code, output)
        self.assertRegex(output, re.compile(r"^unit suite\s+FAIL \(no tests ran\)$", re.MULTILINE))
        self.assertIn("check --all: FAILED (unit suite)", output)

    def test_a_suite_reported_successful_without_a_test_count_fails(self):
        # Interpreters before 3.12 exit 0 when discovery finds nothing.
        suite = ("-m", "unittest", "discover")
        for stderr in ("\n----------------------------------------------------------------------\n"
                       "Ran 0 tests in 0.000s\n\nOK\n", "", "OK\n"):
            with self.subTest(stderr=stderr):
                completed = subprocess.CompletedProcess([], 0, "", stderr)
                self.assertEqual((False, "FAIL (no tests ran)"), check.verdict(suite, completed))

    def test_a_gate_that_is_not_a_test_suite_keeps_a_bare_status(self):
        code, output = self.run_gates((("source check", ("-c", "pass")), ("broken", ("-c", "raise SystemExit(3)"))))
        self.assertEqual(1, code)
        self.assertRegex(output, re.compile(r"^source check\s+PASS$", re.MULTILINE))
        self.assertRegex(output, re.compile(r"^broken\s+FAIL$", re.MULTILINE))
        self.assertIn("check --all: FAILED (broken)", output)


if __name__ == "__main__":
    unittest.main()
