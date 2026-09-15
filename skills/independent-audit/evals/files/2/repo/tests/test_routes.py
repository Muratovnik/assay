import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RouteTests(unittest.TestCase):
    def test_registered_routes(self):
        for registration in sorted((ROOT / "clients").glob("*.json")):
            with self.subTest(client=registration.stem):
                command = json.loads(registration.read_text(encoding="utf-8"))["command"]
                self.assertEqual(command[0], "python")
                result = subprocess.run(
                    [sys.executable, "-B", *command[1:]], cwd=ROOT,
                    capture_output=True, text=True, check=True,
                )
                self.assertEqual(json.loads(result.stdout)["owner"], "runtime")
