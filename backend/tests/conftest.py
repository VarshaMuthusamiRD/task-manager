import os
import tempfile

import pytest
from fastapi.testclient import TestClient

TEST_API_KEY = "test-api-key"


@pytest.fixture
def client(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("TASKS_DB_PATH", path)
    monkeypatch.setenv("API_KEY", TEST_API_KEY)

    from app.main import app

    with TestClient(app, headers={"X-API-Key": TEST_API_KEY}) as test_client:
        yield test_client

    os.remove(path)
