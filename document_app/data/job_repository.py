import json
import sqlite3
from datetime import datetime, timezone


class JobRepository:
    """Reads and writes document-job records in SQLite."""

    def __init__(self, database_path):
        self.database_path = database_path

    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    original_name TEXT NOT NULL,
                    stored_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    result_json TEXT,
                    error_message TEXT
                )
                """
            )

    def create(self, job_id, original_name, stored_name):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO jobs
                    (job_id, original_name, stored_name, status, created_at, updated_at)
                VALUES (?, ?, ?, 'Queued', ?, ?)
                """,
                (job_id, original_name, stored_name, now, now),
            )

    def set_status(self, job_id, status):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                (status, now, job_id),
            )

    def complete(self, job_id, result):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE jobs
                SET status = 'Complete', updated_at = ?, result_json = ?, error_message = NULL
                WHERE job_id = ?
                """,
                (now, json.dumps(result), job_id),
            )

    def fail(self, job_id, message):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE jobs
                SET status = 'Failed', updated_at = ?, error_message = ?
                WHERE job_id = ?
                """,
                (now, message[:300], job_id),
            )

    def get(self, job_id):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        return self._to_dict(row) if row else None

    def list_recent(self, limit=20):
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._to_dict(row) for row in rows]

    @staticmethod
    def _to_dict(row):
        item = dict(row)
        item["result"] = json.loads(item.pop("result_json") or "{}")
        return item
