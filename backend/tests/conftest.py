import os
import tempfile

import pytest
from fastapi.testclient import TestClient

TEST_API_KEY = "test-api-key"


def _temp_db_client(monkeypatch, headers):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("TASKS_DB_PATH", path)

    from app.main import app

    with TestClient(app, headers=headers) as test_client:
        yield test_client

    os.remove(path)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("API_KEY", TEST_API_KEY)
    yield from _temp_db_client(monkeypatch, {"X-API-Key": TEST_API_KEY})


@pytest.fixture
def client_no_server_key(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    yield from _temp_db_client(monkeypatch, {"X-API-Key": TEST_API_KEY})
