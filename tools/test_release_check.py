from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from tools import release_check as rc
from tools import routing_check as gate


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
        provision.assert_called_once_with(self.environment, rc.requirements_digest(), (rc.REQUIREMENTS,))

    def test_the_smoke_names_its_own_environment_and_command(self):
        # The smoke runs in a Git-free snapshot with no ignored files, so it builds
        # its environment in the release tool's scratch directory.
        smoke = self.environment.parent / "smoke-env"
        provision, command = self.run_main(["--environment", str(smoke), "--", "tools/assay.py", "plan",
                                            "--home", "HOME"])
        provision.assert_called_once_with(smoke.resolve(), rc.requirements_digest(), (rc.REQUIREMENTS,))
        self.assertEqual(command, [str(rc.interpreter(smoke.resolve())), "-B", "tools/assay.py", "plan",
                                   "--home", "HOME"])

    def test_named_requirements_build_their_own_environment(self):
        # A gate with more dependencies than the tooling names every file it
        # needs; the environment is current only for all of them together.
        extra = Path(self.directory.name) / "requirements-extra.txt"
        extra.write_text("example==1.0\n", "utf-8")
        files = (rc.REQUIREMENTS, extra)
        self.build(rc.requirements_digest())
        provision, _ = self.run_main(["--requirements", "requirements-tools.txt",
                                      "--requirements", str(extra)])
        provision.assert_called_once_with(self.environment, rc.requirements_digest(files), files)
        self.assertNotEqual(rc.requirements_digest(files), rc.requirements_digest())


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

    def test_every_requirements_file_is_installed(self):
        extra = Path(self.directory.name) / "requirements-extra.txt"
        self.calls.clear()

        def run(command, **_):
            self.calls.append(command)
            if command[1:3] == ["-m", "venv"]:
                rc.interpreter(self.environment).parent.mkdir(parents=True)
            return mock.Mock(returncode=0, stdout="3.14.7\n", stderr="")

        with mock.patch.object(rc.subprocess, "run", side_effect=run):
            rc.provision(self.environment, "digest", (rc.REQUIREMENTS, extra))
        pip = self.calls[-1]
        self.assertEqual(pip[-4:], ["-r", str(rc.REQUIREMENTS), "-r", str(extra)])

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


class RoutingGate(unittest.TestCase):
    """The pre-release gate for the browser and MCP routing integrations."""

    def setUp(self):
        self.calls = []

    def run_inside(self, install_returncode=0, install_output="", suite_stderr="Ran 4 tests in 0.1s\n\nOK\n",
                   suite_returncode=0, version="1.57.0"):
        environment = Path(sys.prefix)

        def run(command, **options):
            self.calls.append((command, options))
            if command[1:4] == ["-m", "playwright", "install"]:
                return mock.Mock(returncode=install_returncode, stdout="", stderr=install_output)
            return mock.Mock(returncode=suite_returncode, stdout="", stderr=suite_stderr)

        with mock.patch.object(gate, "ENVIRONMENT", environment), \
                mock.patch.object(gate.importlib.metadata, "version", return_value=version), \
                mock.patch.object(gate.subprocess, "run", side_effect=run), \
                mock.patch("builtins.print"):
            return gate.main()

    def test_outside_its_environment_the_gate_builds_it_and_runs_itself_there(self):
        # The release tool starts the gate with its own interpreter, which has
        # neither the SDK nor Playwright; the routing environment has both.
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(gate, "ENVIRONMENT", Path(directory) / "routing-env"), \
                mock.patch.object(gate.release_check, "main", return_value=5) as build:
            self.assertEqual(5, gate.main())
        arguments = build.call_args.args[0]
        self.assertEqual(arguments[:2], ["--environment", str(Path(directory) / "routing-env")])
        named = [arguments[index + 1] for index, value in enumerate(arguments) if value == "--requirements"]
        self.assertEqual(named, ["requirements-tools.txt",
                                 "skills/route-subagents/scripts/requirements-mcp.txt",
                                 "skills/route-subagents/scripts/requirements-browser.txt"])
        for name in named:
            self.assertTrue((rc.ROOT / name).is_file(), name)
        self.assertEqual(arguments[-2:], ["--", "tools/routing_check.py"])

    def test_the_browser_goes_into_the_environment_and_the_suites_require_it(self):
        self.assertEqual(0, self.run_inside())
        browsers = str(Path(sys.prefix) / "browsers")
        (install, install_options), *suites = self.calls
        self.assertEqual(install, [sys.executable, "-m", "playwright", "install", "chromium"])
        self.assertEqual(browsers, install_options["env"]["PLAYWRIGHT_BROWSERS_PATH"])
        self.assertEqual([arguments for _, arguments in gate.SUITES],
                         [tuple(command[2:]) for command, _ in suites])
        for command, options in suites:
            with self.subTest(suite=command[-1]):
                self.assertEqual("1", options["env"]["REQUIRE_ROUTING_INTEGRATIONS"])
                self.assertEqual(browsers, options["env"]["PLAYWRIGHT_BROWSERS_PATH"])

    def test_a_browser_that_cannot_be_installed_fails_in_one_line(self):
        output = "Downloading Chromium 143.0 from https://cdn.example/chromium.zip\nError: getaddrinfo ENOTFOUND cdn.example\n"
        with self.assertRaises(SystemExit) as raised:
            self.run_inside(install_returncode=1, install_output=output)
        message = str(raised.exception.code)
        self.assertEqual(1, len(message.splitlines()))
        self.assertIn("Playwright 1.57.0", message)
        self.assertIn("getaddrinfo ENOTFOUND cdn.example", message)
        self.assertEqual(1, len(self.calls), "no suite runs without the browser")

    def test_a_missing_playwright_fails_before_any_install(self):
        with self.assertRaises(SystemExit) as raised, \
                mock.patch.object(gate.importlib.metadata, "version",
                                  side_effect=gate.importlib.metadata.PackageNotFoundError("playwright")), \
                mock.patch.object(gate, "ENVIRONMENT", Path(sys.prefix)), \
                mock.patch.object(gate.subprocess, "run") as run:
            gate.main()
        self.assertIn("Playwright is not installed", str(raised.exception.code))
        run.assert_not_called()

    def test_a_suite_that_fails_or_runs_nothing_fails_the_gate(self):
        self.assertEqual(1, self.run_inside(suite_stderr="Ran 3 tests in 0.1s\n\nFAILED (errors=1)\n",
                                            suite_returncode=1))
        self.calls.clear()
        self.assertEqual(1, self.run_inside(suite_stderr="Ran 0 tests in 0.0s\n\nOK\n"))


if __name__ == "__main__":
    unittest.main()
