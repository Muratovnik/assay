"""Exercise real command receipts; a matching receipt is not task acceptance."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import command_receipt as receipts


class ReceiptReuseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.work = self.root / "work with spaces"
        self.output = self.root / "evidence"
        self.work.mkdir()
        self.output.mkdir()
        (self.work / "source.txt").write_text("required behavior\n", encoding="utf-8")
        self.argv = [sys.executable, "-B", "-c", "print('observed')"]
        self.packet, self.run = receipts.capture(
            self.argv, cwd=self.work, output_parent=self.output,
            inputs=["source.txt"], timeout=10)
        self.retained = self.run["manifest_sha256"]

    def check(self, **changes):
        options = {"argv": self.argv, "cwd": self.work, "inputs": ["source.txt"]}
        options.update(changes)
        return receipts.check_reuse(self.packet, self.retained, **options)

    def test_matching_result_is_read_only_and_not_acceptance(self):
        before = {p.name: p.read_bytes() for p in self.packet.iterdir()}
        with patch.object(receipts.subprocess, "Popen", side_effect=AssertionError("must not execute")):
            result = self.check()
        self.assertEqual("matching-recorded-inputs", result["status"])
        self.assertFalse(result["command_executed"])
        self.assertFalse(result["acceptance_verified"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.packet.iterdir()})

    def test_changed_relevant_bytes_are_rejected(self):
        (self.work / "source.txt").write_text("wrong behavior\n", encoding="utf-8")
        self.assertIn("input_bytes", self.check()["mismatches"])

    def test_unrelated_file_does_not_invalidate_named_inputs(self):
        (self.work / "notes.md").write_text("unrelated note", encoding="utf-8")
        self.assertEqual("matching-recorded-inputs", self.check()["status"])
        self.assertEqual(1, self.check()["inputs_checked"])

    def test_new_required_input_is_not_silently_ignored(self):
        (self.work / "config.json").write_text("{}", encoding="utf-8")
        result = self.check(inputs=["source.txt", "config.json"])
        self.assertIn("input_population", result["mismatches"])

    def test_expected_command_is_exact(self):
        result = self.check(argv=[*self.argv, "another argument"])
        self.assertIn("command", result["mismatches"])

    def test_same_bytes_in_another_directory_are_not_the_same_run(self):
        other = self.root / "other"
        other.mkdir()
        (other / "source.txt").write_bytes((self.work / "source.txt").read_bytes())
        self.assertIn("working_directory", self.check(cwd=other)["mismatches"])

    def test_failed_command_cannot_be_reused_as_success(self):
        argv = [sys.executable, "-B", "-c", "raise SystemExit(3)"]
        packet, run = receipts.capture(argv, cwd=self.work, output_parent=self.output,
                                       inputs=["source.txt"], timeout=10)
        result = receipts.check_reuse(packet, run["manifest_sha256"], argv=argv,
                                      cwd=self.work, inputs=["source.txt"])
        self.assertIn("unsuccessful_run", result["mismatches"])

    def test_input_changed_by_command_is_not_certified(self):
        argv = [sys.executable, "-B", "-c",
                "from pathlib import Path; Path('source.txt').write_text('changed')"]
        packet, run = receipts.capture(argv, cwd=self.work, output_parent=self.output,
                                       inputs=["source.txt"], timeout=10)
        result = receipts.check_reuse(packet, run["manifest_sha256"], argv=argv,
                                      cwd=self.work, inputs=["source.txt"])
        self.assertIn("inputs_changed_during_run", result["mismatches"])

    def test_missing_input_is_unavailable_evidence(self):
        (self.work / "source.txt").unlink()
        with self.assertRaises(OSError):
            self.check()

    def test_empty_duplicate_or_unstructured_expectations_are_invalid(self):
        for options in ({"inputs": []}, {"inputs": "source.txt"},
                        {"inputs": ["source.txt", "./source.txt"]},
                        {"argv": []}, {"argv": "python"}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.check(**options)

    def test_tampering_does_not_refresh_original_receipt(self):
        (self.packet / "stdout.bin").write_bytes(b"different output")
        with self.assertRaises(ValueError):
            self.check()

    def test_cli_distinguishes_match_mismatch_and_unavailable(self):
        command = [sys.executable, "-B", str(Path(receipts.__file__).resolve()), "reuse",
                   "--receipt", str(self.packet), "--manifest-sha256", self.retained,
                   "--cwd", str(self.work), "--input", "source.txt", "--", *self.argv]
        matched = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(0, matched.returncode, matched.stderr)
        self.assertFalse(json.loads(matched.stdout)["acceptance_verified"])
        (self.work / "source.txt").write_text("changed", encoding="utf-8")
        stale = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(1, stale.returncode, stale.stderr)
        self.assertEqual("not-reusable", json.loads(stale.stdout)["status"])
        (self.work / "source.txt").unlink()
        missing = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(2, missing.returncode)
        self.assertEqual("", missing.stdout)


if __name__ == "__main__":
    unittest.main()
