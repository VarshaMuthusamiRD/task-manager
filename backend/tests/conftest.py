import os
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("TASKS_DB_PATH", path)

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client

    os.remove(path)
