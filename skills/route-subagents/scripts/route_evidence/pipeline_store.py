"""Short-lived hook/MCP rendezvous using SQLite transactions, not a task database."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

from .core import EvidenceError, encoded
from .pipeline_config import plain_path

SCHEMA = 2
MAX_RECORDS = 2048
MAX_PAYLOAD = 512 * 1024


class PipelineStore:
    def __init__(self, directory: Path, *, clock: Callable = time.time):
        self.directory = plain_path(directory)
        self.path = self.directory / "routing-v2.sqlite3"
        self.clock = clock

    @contextmanager
    def transaction(self):
        plain_path(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        plain_path(self.path)
        for suffix in ("-journal", "-wal", "-shm"):
            plain_path(Path(str(self.path) + suffix))
        db = sqlite3.connect(self.path, timeout=2, isolation_level=None)
        try:
            if os.name != "nt":
                self.path.chmod(0o600)
            db.execute("PRAGMA secure_delete=ON")
            db.execute("BEGIN IMMEDIATE")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, SCHEMA):
                raise EvidenceError("pipeline_store_version_mismatch")
            db.execute("CREATE TABLE IF NOT EXISTS records (kind TEXT NOT NULL, id TEXT NOT NULL, "
                       "payload TEXT NOT NULL, expires REAL NOT NULL, PRIMARY KEY(kind,id))")
            db.execute(f"PRAGMA user_version={SCHEMA}")
            db.execute("DELETE FROM records WHERE expires <= ?", (self.clock(),))
            yield Transaction(db, self.clock)
            db.commit()
        except sqlite3.Error as exc:
            db.rollback()
            raise EvidenceError("pipeline_store_unavailable") from exc
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()


class Transaction:
    def __init__(self, db, clock):
        self.db, self.clock = db, clock

    def get(self, kind: str, key: str):
        row = self.db.execute("SELECT payload FROM records WHERE kind=? AND id=?", (kind, key)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, kind: str, key: str, value: dict, expires: float):
        payload = encoded(value)
        if len(payload) > MAX_PAYLOAD or expires <= self.clock():
            raise EvidenceError("pipeline_record_bound_or_expiry")
        if self.get(kind, key) is None and self.db.execute("SELECT count(*) FROM records").fetchone()[0] >= MAX_RECORDS:
            raise EvidenceError("pipeline_store_full")
        self.db.execute("INSERT INTO records VALUES (?,?,?,?) ON CONFLICT(kind,id) DO UPDATE "
                        "SET payload=excluded.payload, expires=excluded.expires",
                        (kind, key, payload.decode("utf-8"), expires))

    def delete(self, kind: str, key: str):
        self.db.execute("DELETE FROM records WHERE kind=? AND id=?", (kind, key))

    def values(self, kind: str):
        return [json.loads(row[0]) for row in self.db.execute("SELECT payload FROM records WHERE kind=?", (kind,))]
