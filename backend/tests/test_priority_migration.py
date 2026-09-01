import os
import sqlite3
import tempfile

from app.db import get_connection, init_db


def _create_legacy_schema(path):
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'todo',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO tasks (title, description, status, created_at, updated_at) "
        "VALUES ('Pre-existing task', '', 'todo', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00')"
    )
    conn.commit()
    conn.close()


def test_init_db_backfills_priority_column_on_legacy_database(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _create_legacy_schema(path)
    monkeypatch.setenv("TASKS_DB_PATH", path)

    conn = get_connection()
    try:
        init_db(conn)
        row = conn.execute("SELECT priority FROM tasks WHERE title = 'Pre-existing task'").fetchone()
        assert row["priority"] == "medium"
    finally:
        conn.close()
        os.remove(path)


def test_init_db_is_idempotent_on_already_migrated_database(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("TASKS_DB_PATH", path)

    conn = get_connection()
    try:
        init_db(conn)
        init_db(conn)  # must not raise "duplicate column" on second call
    finally:
        conn.close()
        os.remove(path)
