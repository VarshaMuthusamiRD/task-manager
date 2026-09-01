import os
import tempfile

from app.crud import create_task, update_task
from app.db import get_connection, init_db
from app.models import TaskCreate, TaskUpdate


def test_create_task_persists_the_given_priority(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("TASKS_DB_PATH", path)

    conn = get_connection()
    try:
        init_db(conn)
        created = create_task(conn, TaskCreate(title="Task", priority="high"))
        assert created["priority"] == "high"
    finally:
        conn.close()
        os.remove(path)


def test_update_task_persists_the_new_priority(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("TASKS_DB_PATH", path)

    conn = get_connection()
    try:
        init_db(conn)
        created = create_task(conn, TaskCreate(title="Task", priority="low"))
        updated = update_task(
            conn,
            created["id"],
            TaskUpdate(title="Task", priority="high"),
        )
        assert updated["priority"] == "high"
    finally:
        conn.close()
        os.remove(path)
