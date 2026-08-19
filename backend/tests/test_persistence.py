import os
import tempfile

from app.crud import create_task, list_tasks
from app.db import get_connection, init_db
from app.models import TaskCreate


def test_data_survives_reopening_the_database(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("TASKS_DB_PATH", path)

    try:
        first_conn = get_connection()
        init_db(first_conn)
        create_task(first_conn, TaskCreate(title="Survive restart"))
        first_conn.close()

        second_conn = get_connection()
        init_db(second_conn)
        tasks = list_tasks(second_conn)
        second_conn.close()

        assert len(tasks) == 1
        assert tasks[0]["title"] == "Survive restart"
    finally:
        os.remove(path)
