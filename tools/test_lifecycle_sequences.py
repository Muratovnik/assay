"""Exercise before/after failure at every planned install and uninstall entry."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import assay as aa
from tools.test_assay import write_fixture


def observed(home: Path) -> dict[str, tuple[str, object]]:
    # Directories created to hold managed entries need not disappear on rollback.
    result = {}
    for path in home.rglob("*"):
        if path.is_symlink():
            result[path.relative_to(home).as_posix()] = ("link", str(aa.link_destination(path)))
        elif path.is_file():
            result[path.relative_to(home).as_posix()] = ("file", path.read_bytes())
    return result


class LifecycleSequenceTests(unittest.TestCase):
    def test_each_entry_failure_restores_observed_owned_vector(self) -> None:
        for operation in ("install", "uninstall"):
            for phase in ("before", "after"):
                # Fixture has one skill and two profiles, each with two projections.
                for failure_index in range(1, 7):
                    with self.subTest(operation=operation, phase=phase, at=failure_index), tempfile.TemporaryDirectory() as directory:
                        base = Path(directory)
                        source, home = base / "source", base / "home"
                        source.mkdir()
                        home.mkdir()
                        write_fixture(source)
                        sentinel = home / ".codex/skills/.system/foreign.txt"
                        sentinel.parent.mkdir(parents=True)
                        sentinel.write_bytes(b"keep")
                        if operation == "uninstall":
                            aa.install_links(source, home)
                        before = observed(home)
                        function = "create_entry" if operation == "install" else "remove_entry"
                        real = getattr(aa, function)
                        calls = 0

                        def fail_once(*args):
                            nonlocal calls
                            calls += 1
                            if calls == failure_index and phase == "before":
                                raise OSError("sequence fault")
                            real(*args)
                            if calls == failure_index and phase == "after":
                                raise OSError("sequence fault")

                        with mock.patch.object(aa, function, side_effect=fail_once), self.assertRaisesRegex(OSError, "sequence fault"):
                            (aa.install_links if operation == "install" else aa.uninstall_links)(source, home)
                        self.assertEqual(before, observed(home))
                        self.assertEqual(b"keep", sentinel.read_bytes())

    def test_repeated_install_uninstall_and_foreign_edit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, home = base / "source", base / "home"
            source.mkdir()
            home.mkdir()
            write_fixture(source)
            aa.install_links(source, home)
            installed = observed(home)
            self.assertTrue(all(x.startswith("NOOP ") for x in aa.install_links(source, home)))
            self.assertEqual(installed, observed(home))
            adapter = home / ".codex/agents/evidence-reviewer.toml"
            adapter.write_bytes(b"local edit")
            edited = observed(home)
            for operation in (aa.install_links, aa.uninstall_links):
                with self.assertRaises(aa.ContractError):
                    operation(source, home)
                self.assertEqual(edited, observed(home))
            adapter.write_bytes(installed[".codex/agents/evidence-reviewer.toml"][1])
            aa.uninstall_links(source, home)
            self.assertTrue(all(x.startswith("MISSING ") for x in aa.uninstall_links(source, home)))
            self.assertEqual({}, observed(home))

    def test_rollback_failure_is_reported_and_not_called_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, home = base / "source", base / "home"
            source.mkdir()
            home.mkdir()
            write_fixture(source)
            real = aa.create_entry

            def created_then_failed(*args):
                real(*args)
                raise OSError("initial fault")

            with (mock.patch.object(aa, "create_entry", side_effect=created_then_failed),
                  mock.patch.object(aa, "remove_entry", side_effect=OSError("rollback fault")),
                  self.assertRaisesRegex(aa.ContractError, "rollback was incomplete")):
                aa.install_links(source, home)
            self.assertTrue(observed(home))


if __name__ == "__main__":
    unittest.main()
