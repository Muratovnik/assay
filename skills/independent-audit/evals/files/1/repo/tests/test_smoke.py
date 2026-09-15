import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SmokeTests(unittest.TestCase):
    def test_launcher(self):
        result = subprocess.run(
            [sys.executable, "-B", "runtime/launcher.py"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        self.assertEqual(json.loads(result.stdout)["owner"], "runtime")

    def test_valid_config(self):
        result = subprocess.run(
            [sys.executable, "-B", "tools/validate.py", "configs/valid.json"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "OK")
