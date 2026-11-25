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


class ReleaseCheckInterpreter(unittest.TestCase):
    """Which Python builds the environment, and how an unsupported one is refused."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.environment = (Path(self.directory.name) / "tools-env").resolve()
        self.calls = []

    def provision(self, version="3.14.7", pip_returncode=0, pip_output="", named=None):
        def run(command, **_):
            self.calls.append(command)
            if command[1:3] == ["-m", "venv"]:
                rc.interpreter(self.environment).parent.mkdir(parents=True)
                return mock.Mock(returncode=0)
            if command[1:2] == ["-c"]:
                return mock.Mock(returncode=0, stdout=version + "\n", stderr="")
            return mock.Mock(returncode=pip_returncode, stdout="", stderr=pip_output)

        variables = {rc.PYTHON_VARIABLE: named} if named else {}
        with mock.patch.dict(rc.os.environ, variables), mock.patch.object(rc.subprocess, "run", side_effect=run):
            if named is None:
                rc.os.environ.pop(rc.PYTHON_VARIABLE, None)
            rc.provision(self.environment, "digest")

    def test_the_environment_takes_prebuilt_wheels_only(self):
        # A missing wheel must not turn into a native build that needs a compiler.
        self.provision()
        pip = self.calls[-1]
        self.assertEqual(pip[:3], [str(rc.interpreter(self.environment)), "-m", "pip"])
        self.assertEqual(pip[pip.index("--only-binary") + 1], ":all:")
        self.assertEqual("digest\n", (self.environment / rc.STAMP).read_text("utf-8"))

    def test_the_running_interpreter_builds_the_environment_by_default(self):
        self.provision()
        self.assertEqual(self.calls[1], [rc.sys.executable, "-m", "venv", str(self.environment)])

    def test_a_named_interpreter_builds_the_environment(self):
        self.provision(named="/opt/python3.11/bin/python")
        self.assertEqual(self.calls[0][0], "/opt/python3.11/bin/python")
        self.assertEqual(self.calls[1], ["/opt/python3.11/bin/python", "-m", "venv", str(self.environment)])

    def test_missing_wheels_are_refused_in_one_line_naming_the_way_out(self):
        output = ("ERROR: Could not find a version that satisfies the requirement PyYAML==6.0.3\n"
                  "ERROR: No matching distribution found for PyYAML==6.0.3\n")
        with self.assertRaises(SystemExit) as raised:
            self.provision(version="3.15.2", pip_returncode=1, pip_output=output)
        message = str(raised.exception.code)
        self.assertEqual(1, len(message.splitlines()))
        self.assertIn("Python 3.15.2", message)
        self.assertIn("No matching distribution found for PyYAML==6.0.3", message)
        self.assertIn(rc.PYTHON_VARIABLE, message)
        # No half-built environment is left to be mistaken for a current one.
        self.assertFalse(self.environment.exists())

    def test_an_interpreter_older_than_the_tooling_needs_is_refused_before_building(self):
        with self.assertRaises(SystemExit) as raised:
            self.provision(version="3.10.14")
        self.assertIn("older than 3.11", str(raised.exception.code))
        self.assertEqual(1, len(self.calls))


if __name__ == "__main__":
    unittest.main()
