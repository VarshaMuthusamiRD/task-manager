import os
import tempfile

from app.crud import create_task, list_tasks
from app.db import get_connection, get_db_path, init_db
from app.models import TaskCreate


def test_request_recreates_schema_if_db_file_was_deleted(client):
    os.remove(get_db_path())

    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_data_survives_reopening_the_database(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("TASKS_DB_PATH", path)

    try:
        first_conn = get_connection()
        init_db(first_conn)
        create_task(first_conn, TaskCreate(title="Survive restart", priority="medium"))
        first_conn.close()

        second_conn = get_connection()
        init_db(second_conn)
        tasks = list_tasks(second_conn)
        second_conn.close()

        assert len(tasks) == 1
        assert tasks[0]["title"] == "Survive restart"
    finally:
        os.remove(path)
