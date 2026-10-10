from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import types
import unittest
import zipfile


class EvidenceRestoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        archive = Path(__file__).resolve().parents[1] / (
            "skills/technical-writing/evals/task-completion-evidence.zip"
        )
        with zipfile.ZipFile(archive) as source:
            helper = source.read("assemble.py")
        cls.helper = types.ModuleType("assay_evidence_restore_test")
        exec(compile(helper, "evidence.zip!assemble.py", "exec"), cls.helper.__dict__)

    def fixture(self, root: Path, change: dict | None = None, missing: str | None = None) -> Path:
        rows = []
        blobs = {}
        for name, data, mode in (
            ("first.txt", b"first", 0o444),
            ("second.txt", b"second", 0o644),
            ("executable.txt", b"executable", 0o755),
        ):
            digest = hashlib.sha256(data).hexdigest()
            rows.append({"logical_path": name, "bytes": len(data), "sha256": digest, "mode": mode})
            blobs["blobs/sha256/" + digest] = data
        if change:
            rows[1].update(change)
        if missing:
            del rows[1][missing]
        archive = root / "evidence.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("manifest.json", json.dumps({"schema": self.helper.SCHEMA, "files": rows}))
            for name, data in blobs.items():
                output.writestr(name, data)
        return archive

    def test_valid_ordinary_modes_preserve_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "restored"
            self.assertEqual(3, self.helper.restore(self.fixture(root), destination))
            for name, data, mode in (
                ("first.txt", b"first", 0o444),
                ("second.txt", b"second", 0o644),
                ("executable.txt", b"executable", 0o755),
            ):
                path = destination / name
                self.assertEqual(data, path.read_bytes())
                if os.name != "nt":
                    self.assertEqual(mode, stat.S_IMODE(path.stat().st_mode))
                else:
                    self.assertEqual(bool(mode & stat.S_IWRITE), bool(path.stat().st_mode & stat.S_IWRITE))
                    path.chmod(0o644)

    def test_incomplete_rows_are_rejected_before_destination_creation(self) -> None:
        for field in ("logical_path", "sha256", "bytes", "mode"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                destination = root / "restored"
                archive = self.fixture(root, missing=field)
                with self.assertRaises(ValueError):
                    self.helper.restore(archive, destination)
                self.assertFalse(destination.exists())

    def test_invalid_scalar_fields_leave_existing_empty_destination_untouched(self) -> None:
        for change in (
            {"mode": "644"}, {"mode": True}, {"mode": 420.0},
            {"mode": -1}, {"mode": 0o1000}, {"mode": 0o100644},
            {"bytes": True}, {"bytes": 6.0}, {"bytes": -1},
        ):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                destination = root / "restored"
                destination.mkdir()
                archive = self.fixture(root, change=change)
                with self.assertRaises(ValueError):
                    self.helper.restore(archive, destination)
                self.assertEqual([], list(destination.iterdir()))


if __name__ == "__main__":
    unittest.main()
