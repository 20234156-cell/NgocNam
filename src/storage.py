"""Local persistent workflow store. SQLite transactions serialize competing decisions."""
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WorkflowStore:
    def __init__(self, path=None):
        self.path = str(path or os.environ.get("CREDIT_DB_PATH", ROOT / "runtime" / "credit.sqlite3"))

    def connect(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, role TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY, username TEXT NOT NULL REFERENCES users(username), expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS login_attempts (
                source TEXT PRIMARY KEY, count INTEGER NOT NULL, since REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS assessments (
                request_id TEXT PRIMARY KEY, case_id TEXT NOT NULL, fingerprint TEXT NOT NULL,
                created REAL NOT NULL, run INTEGER NOT NULL, response TEXT NOT NULL,
                UNIQUE(case_id, run));
            CREATE INDEX IF NOT EXISTS assessment_case ON assessments(case_id, run DESC);
            CREATE TABLE IF NOT EXISTS committee (
                decision_id TEXT PRIMARY KEY, assessment_id TEXT NOT NULL UNIQUE REFERENCES assessments(request_id),
                idempotency_key TEXT NOT NULL UNIQUE, fingerprint TEXT NOT NULL, response TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS core_simulations (
                simulation_id TEXT PRIMARY KEY, decision_id TEXT NOT NULL UNIQUE REFERENCES committee(decision_id),
                idempotency_key TEXT NOT NULL UNIQUE, fingerprint TEXT NOT NULL, response TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT NOT NULL UNIQUE,
                record TEXT NOT NULL);
            CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit_events
                BEGIN SELECT RAISE(ABORT, 'audit events are append-only'); END;
            CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit_events
                BEGIN SELECT RAISE(ABORT, 'audit events are append-only'); END;
        """)
        # Existing records remain untouched; corrections must be new linked runs.
        for table in ("assessments", "committee", "core_simulations"):
            for operation in ("UPDATE", "DELETE"):
                db.execute(f"""CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()}
                    BEFORE {operation} ON {table}
                    BEGIN SELECT RAISE(ABORT, 'workflow records are append-only'); END""")
        return db

    @contextmanager
    def transaction(self):
        db = self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def recent_events(self, limit=100):
        with self.transaction() as db:
            return [json.loads(r[0]) for r in db.execute(
                "SELECT record FROM audit_events ORDER BY sequence DESC LIMIT ?", (limit,))]


store = WorkflowStore()
