from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools import manifest_copy as mc

TRACKED = {
    "AGENTS.md": b"# Instructions\n",
    "skills/demo/SKILL.md": b"---\nname: demo\n---\n",
    "skills/demo/references/notes.md": b"Notes.\n",
    "tools/run.py": b"print('run')\n",
}


def git(repository: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(repository), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    *arguments], check=True, capture_output=True)


@unittest.skipUnless(shutil.which("git"), "needs Git to build a revision")
class ManifestCopyTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        base = Path(directory.name)
        self.repository = base / "repository"
        self.installed = base / "cache" / "1.0.0"
        self.output = base / "snapshot"
        for root in (self.repository, self.installed):
            for relative, data in TRACKED.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        subprocess.run(["git", "init", "-q", str(self.repository)], check=True)
        git(self.repository, "add", ".")
        git(self.repository, "commit", "-q", "-m", "release")
        git(self.repository, "tag", "v1.0.0")

    def add(self, relative: str, data: bytes = b"x\n") -> None:
        path = self.installed / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def copied(self) -> set[str]:
        tree = self.output / mc.TREE
        return {path.relative_to(tree).as_posix() for path in tree.rglob("*") if path.is_file()}

    def test_only_the_revision_files_are_copied_from_a_tree_holding_a_checkout(self):
        # A cache that points at a checkout carries its Git metadata and its
        # ignored evidence, earlier snapshots with their own .git included.
        self.add(".git/HEAD", b"ref: refs/heads/main\n")
        self.add(".git/objects/ab/cdef", b"\x78\x01")
        self.add(".private/release/before/trees/cache/.git/config")
        self.add(".private/release/before/trees/cache/AGENTS.md")
        self.add(".in_use/4242", b"")
        self.add("skills/demo/references/draft.md")

        report = mc.copy_by_manifest(self.repository, "v1.0.0", self.installed, self.output)

        self.assertEqual(set(TRACKED), self.copied())
        for relative, data in TRACKED.items():
            self.assertEqual(data, (self.output / mc.TREE / relative).read_bytes())
        self.assertEqual({"same"}, {entry["status"] for entry in report["files"]})
        self.assertEqual(
            [(".git/", 2), (".in_use/", 1), (".private/", 2), ("skills/demo/references/draft.md", 1)],
            sorted((entry["path"], entry["files"]) for entry in report["unlisted"]))
        written = json.loads((self.output / mc.REPORT).read_text("utf-8"))
        self.assertEqual(written, report)
        self.assertEqual(40, len(report["revision"]))

    def test_changed_and_missing_installed_files_are_recorded(self):
        # The snapshot keeps the bytes the client really has, and says where
        # they differ from the release.
        self.add("AGENTS.md", b"# Edited by hand\n")
        (self.installed / "tools/run.py").unlink()

        report = mc.copy_by_manifest(self.repository, "v1.0.0", self.installed, self.output)

        status = {entry["path"]: entry["status"] for entry in report["files"]}
        self.assertEqual("changed", status["AGENTS.md"])
        self.assertEqual("missing", status["tools/run.py"])
        self.assertEqual(b"# Edited by hand\n", (self.output / mc.TREE / "AGENTS.md").read_bytes())
        self.assertNotIn("tools/run.py", self.copied())

    def test_unusable_inputs_are_refused_with_their_own_exit_code(self):
        cases = {
            "unknown revision": ["--revision", "v9.9.9", "--source", str(self.installed)],
            "missing tree": ["--revision", "v1.0.0", "--source", str(self.installed.parent / "absent")],
            "output inside the tree": ["--revision", "v1.0.0", "--source", str(self.installed),
                                       "--output", str(self.installed / "snapshot")],
        }
        for label, arguments in cases.items():
            with self.subTest(label), contextlib.redirect_stderr(io.StringIO()) as error:
                if "--output" not in arguments:
                    arguments = [*arguments, "--output", str(self.output)]
                self.assertEqual(2, mc.main([*arguments, "--repository", str(self.repository)]))
                self.assertTrue(error.getvalue().startswith("manifest copy: "))
        self.assertFalse(self.output.exists())
        self.assertFalse((self.installed / "snapshot").exists())

    def test_an_existing_output_is_never_written_into(self):
        self.output.mkdir()
        (self.output / "kept.txt").write_bytes(b"kept\n")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(2, mc.main(["--revision", "v1.0.0", "--source", str(self.installed),
                                         "--output", str(self.output), "--repository", str(self.repository)]))
        self.assertEqual(["kept.txt"], [path.name for path in self.output.iterdir()])

    def test_the_command_line_writes_the_snapshot_and_a_one_line_summary(self):
        self.add(".git/HEAD")
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, mc.main(["--revision", "v1.0.0", "--source", str(self.installed),
                                         "--output", str(self.output), "--repository", str(self.repository)]))
        line = output.getvalue().strip()
        self.assertEqual(1, len(line.splitlines()))
        self.assertIn("4 same", line)
        self.assertIn("1 unlisted paths (1 files) not copied", line)


if __name__ == "__main__":
    unittest.main()
