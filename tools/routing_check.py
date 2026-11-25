"""Run the routing integration suites with their real browser and MCP SDK.

`check --all` runs in the tooling environment, which carries neither
Playwright nor the MCP SDK, so the browser adapter and the stdio MCP service
are skipped there. This gate runs before a release instead. It builds its own
pinned environment in the ignored `.cache/routing-check-env` through
`release_check.py`, installs the Chromium build the pinned Playwright expects
into that environment's `browsers` directory, and runs the suites with
REQUIRE_ROUTING_INTEGRATIONS=1, so a missing SDK or browser fails rather than
skips. A browser that cannot be installed fails the gate in one line that
names the Playwright version and the reason. Nothing is installed elsewhere.
"""
from __future__ import annotations

import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys

if __package__:
    from . import release_check
else:
    import release_check

ROOT = release_check.ROOT
# A directory of its own: `.cache/routing-env` is where a checkout's registered
# routing service may be running from, and a rebuild deletes its environment.
ENVIRONMENT = ROOT / ".cache" / "routing-check-env"
SCRIPTS = Path("skills/route-subagents/scripts")
REQUIREMENTS = (
    Path("requirements-tools.txt"),
    SCRIPTS / "requirements-mcp.txt",
    SCRIPTS / "requirements-browser.txt",
)
ENTRY = "tools/routing_check.py"
# The suites the hosted routing workflow runs: every benchmark module with the
# real browser and SDK required, then the routing modules with the SDK present.
SUITES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("routing integrations", ("-m", "unittest", "discover", "-s", "tools", "-p", "test_benchmark*.py")),
    ("routing tests", ("-m", "unittest", "discover", "-s", "tools", "-p", "test_routing*.py")),
)


def inside(environment: Path) -> bool:
    return Path(sys.prefix).resolve() == environment.resolve()


def browsers(environment: Path) -> Path:
    return environment / "browsers"


def gate_variables(environment: Path) -> dict[str, str]:
    return dict(os.environ, REQUIRE_ROUTING_INTEGRATIONS="1",
                PLAYWRIGHT_BROWSERS_PATH=str(browsers(environment)))


def install_browser(variables: dict[str, str]) -> None:
    """Install, or confirm, the Chromium build of the installed Playwright."""
    try:
        version = importlib.metadata.version("playwright")
    except importlib.metadata.PackageNotFoundError:
        raise SystemExit("routing check: Playwright is not installed in the routing environment") from None
    completed = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                               env=variables, capture_output=True, text=True, check=False)
    if completed.returncode:
        reason = release_check.last_error(completed.stdout + completed.stderr)
        raise SystemExit(f"routing check: cannot install Chromium for Playwright {version}: {reason}")


def run_suites(variables: dict[str, str]) -> int:
    # The tooling's own dependencies are present in this environment.
    if __package__:
        from .check import verdict
    else:
        from check import verdict

    failed: list[str] = []
    for label, arguments in SUITES:
        completed = subprocess.run([sys.executable, "-B", *arguments], cwd=ROOT, env=variables,
                                   capture_output=True, text=True, check=False)
        passed, status = verdict(arguments, completed)
        print(f"{label:24} {status}", flush=True)
        if not passed:
            failed.append(label)
            output = (completed.stdout + completed.stderr).strip()
            if output:
                print("\n".join(f"    {line}" for line in output.splitlines()), flush=True)
    print()
    if failed:
        print(f"routing check: FAILED ({', '.join(failed)})")
        return 1
    print("routing check: PASS")
    return 0


def main() -> int:
    if not inside(ENVIRONMENT):
        # Any interpreter may start the gate; the routing environment runs it.
        arguments = ["--environment", str(ENVIRONMENT)]
        for path in REQUIREMENTS:
            arguments += ["--requirements", path.as_posix()]
        return release_check.main([*arguments, "--", ENTRY])
    variables = gate_variables(ENVIRONMENT)
    install_browser(variables)
    return run_suites(variables)


if __name__ == "__main__":
    raise SystemExit(main())
