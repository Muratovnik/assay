from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import release_check as rc


class ReleaseCheckEnvironment(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.environment = Path(self.directory.name) / "tools-env"

    def build(self, digest):
        python = rc.interpreter(self.environment)
        python.parent.mkdir(parents=True)
        python.write_bytes(b"")
        (self.environment / rc.STAMP).write_text(digest + "\n", "utf-8")

    def test_an_environment_is_current_only_for_the_requirements_it_was_built_from(self):
        self.assertFalse(rc.current(self.environment, "a"))
        self.build("a")
        self.assertTrue(rc.current(self.environment, "a"))
        self.assertFalse(rc.current(self.environment, "b"))

    def test_a_current_environment_is_reused_and_check_all_runs_inside_it(self):
        self.build(rc.requirements_digest())
        with mock.patch.object(rc, "ENVIRONMENT", self.environment), \
                mock.patch.object(rc, "provision") as provision, \
                mock.patch.object(rc.subprocess, "run", return_value=mock.Mock(returncode=3)) as run:
            self.assertEqual(rc.main(), 3)
        provision.assert_not_called()
        command = run.call_args.args[0]
        self.assertEqual(command[0], str(rc.interpreter(self.environment)))
        self.assertEqual(command[-2:], [str(rc.ROOT / "tools" / "check.py"), "--all"])

    def test_changed_requirements_rebuild_the_environment(self):
        self.build("stale")
        with mock.patch.object(rc, "ENVIRONMENT", self.environment), \
                mock.patch.object(rc, "provision") as provision, \
                mock.patch.object(rc.subprocess, "run", return_value=mock.Mock(returncode=0)):
            self.assertEqual(rc.main(), 0)
        provision.assert_called_once_with(self.environment, rc.requirements_digest())


if __name__ == "__main__":
    unittest.main()
