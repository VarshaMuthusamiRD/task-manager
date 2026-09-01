import os
import sqlite3

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tasks.db")


def get_db_path() -> str:
    return os.environ.get("TASKS_DB_PATH", DEFAULT_DB_PATH)


def get_connection() -> sqlite3.Connection:
    path = get_db_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'todo',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    _migrate_add_priority_column(conn)
    conn.commit()


def _migrate_add_priority_column(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
    if "priority" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'")
