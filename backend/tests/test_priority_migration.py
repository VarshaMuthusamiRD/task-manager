import os
import sqlite3
import tempfile

import pytest

from app.db import _migrate_add_priority_column, get_connection, init_db


class _FakeConnection:
    """Stands in for a sqlite3.Connection to deterministically force the
    migration helper down its exception-handling branch — real concurrent
    SQLite connections can't be forced into that interleaving reliably in a
    single-threaded test."""

    def __init__(self, existing_columns, alter_error=None):
        self._existing_columns = existing_columns
        self._alter_error = alter_error

    def execute(self, sql, *args):
        if sql.strip().startswith("PRAGMA table_info"):
            return [{"name": name} for name in self._existing_columns]
        if sql.strip().startswith("ALTER TABLE") and self._alter_error:
            raise self._alter_error
        return []


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


def test_migrate_add_priority_column_swallows_concurrent_duplicate_column_error():
    # Simulates two requests racing to migrate the same legacy database: this
    # connection's PRAGMA check saw no "priority" column, but another
    # connection already added it and committed before this ALTER ran.
    fake_conn = _FakeConnection(
        existing_columns=["id", "title"],
        alter_error=sqlite3.OperationalError("duplicate column name: priority"),
    )

    _migrate_add_priority_column(fake_conn)  # must not raise


def test_migrate_add_priority_column_reraises_unrelated_operational_errors():
    fake_conn = _FakeConnection(
        existing_columns=["id", "title"],
        alter_error=sqlite3.OperationalError("database is locked"),
    )

    with pytest.raises(sqlite3.OperationalError, match="database is locked"):
        _migrate_add_priority_column(fake_conn)
