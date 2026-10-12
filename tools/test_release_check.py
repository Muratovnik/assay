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
        self.environment = (Path(self.directory.name) / "tools-env").resolve()

    def build(self, digest):
        python = rc.interpreter(self.environment)
        python.parent.mkdir(parents=True)
        python.write_bytes(b"")
        (self.environment / rc.STAMP).write_text(digest + "\n", "utf-8")

    def run_main(self, argv, returncode=0):
        with mock.patch.object(rc, "ENVIRONMENT", self.environment), \
                mock.patch.object(rc, "provision") as provision, \
                mock.patch.object(rc.subprocess, "run", return_value=mock.Mock(returncode=returncode)) as run:
            self.assertEqual(rc.main(argv), returncode)
        return provision, run.call_args.args[0]

    def test_an_environment_is_current_only_for_the_requirements_it_was_built_from(self):
        self.assertFalse(rc.current(self.environment, "a"))
        self.build("a")
        self.assertTrue(rc.current(self.environment, "a"))
        self.assertFalse(rc.current(self.environment, "b"))

    def test_a_current_environment_is_reused_and_check_all_runs_inside_it(self):
        self.build(rc.requirements_digest())
        provision, command = self.run_main([], returncode=3)
        provision.assert_not_called()
        self.assertEqual(command, [str(rc.interpreter(self.environment)), "-B", "tools/check.py", "--all"])

    def test_changed_requirements_rebuild_the_environment(self):
        self.build("stale")
        provision, _ = self.run_main([])
        provision.assert_called_once_with(self.environment, rc.requirements_digest())

    def test_the_smoke_names_its_own_environment_and_command(self):
        # The smoke runs in a Git-free snapshot with no ignored files, so it builds
        # its environment in the release tool's scratch directory.
        smoke = self.environment.parent / "smoke-env"
        provision, command = self.run_main(["--environment", str(smoke), "--", "tools/assay.py", "plan",
                                            "--home", "HOME"])
        provision.assert_called_once_with(smoke.resolve(), rc.requirements_digest())
        self.assertEqual(command, [str(rc.interpreter(smoke.resolve())), "-B", "tools/assay.py", "plan",
                                   "--home", "HOME"])


if __name__ == "__main__":
    unittest.main()
