"""Owner configuration must not be resolved relative to an arbitrary project."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "skills/route-subagents/scripts"))
from runtime import cli


class HookOptionsTests(unittest.TestCase):
    def test_relative_config_is_rejected_before_reading_project_files(self):
        for location in ("hooks.json", "../hooks.json"):
            with self.subTest(location=location), patch.object(cli, "read_json") as read:
                with self.assertRaisesRegex(ValueError, "absolute"):
                    cli.options({"ASSAY_HOOK_CONFIG": location})
                read.assert_not_called()

    def test_explicit_absolute_config_remains_supported(self):
        location = str(ROOT / "owner-hook-config.json")
        with patch.object(cli, "read_json", return_value={"record_events": True}) as read:
            settings = cli.options({"ASSAY_HOOK_CONFIG": location})
        read.assert_called_once_with(location)
        self.assertTrue(settings["record_events"])
        self.assertIsNone(settings["state_dir"])


if __name__ == "__main__":
    unittest.main()
