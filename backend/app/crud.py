import sqlite3
from datetime import datetime, timezone

from app.models import TaskCreate, TaskUpdate


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def create_task(conn: sqlite3.Connection, task: TaskCreate) -> dict:
    now = _now_iso()
    cursor = conn.execute(
        """
        INSERT INTO tasks (title, description, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (task.title, task.description, task.status.value, now, now),
    )
    conn.commit()
    return get_task(conn, cursor.lastrowid)


def list_tasks(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM tasks ORDER BY created_at ASC").fetchall()
    return [_row_to_dict(row) for row in rows]


def get_task(conn: sqlite3.Connection, task_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _row_to_dict(row) if row else None


def update_task(conn: sqlite3.Connection, task_id: int, task: TaskUpdate) -> dict | None:
    if get_task(conn, task_id) is None:
        return None
    conn.execute(
        """
        UPDATE tasks SET title = ?, description = ?, status = ?, updated_at = ?
        WHERE id = ?
        """,
        (task.title, task.description, task.status.value, _now_iso(), task_id),
    )
    conn.commit()
    return get_task(conn, task_id)


def delete_task(conn: sqlite3.Connection, task_id: int) -> bool:
    if get_task(conn, task_id) is None:
        return False
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    return True
