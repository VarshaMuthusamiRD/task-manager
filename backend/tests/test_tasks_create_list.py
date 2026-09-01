def test_list_empty_db_returns_empty_array(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_create_task_happy_path(client):
    payload = {"title": "Buy milk", "description": "2% preferred", "status": "todo", "priority": "high"}
    response = client.post("/tasks", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Buy milk"
    assert body["description"] == "2% preferred"
    assert body["status"] == "todo"
    assert body["priority"] == "high"
    assert isinstance(body["id"], int)
    assert body["created_at"] == body["updated_at"]


def test_create_task_missing_title_returns_422(client):
    response = client.post("/tasks", json={"description": "no title here", "priority": "medium"})
    assert response.status_code == 422


def test_create_task_invalid_status_returns_422(client):
    response = client.post("/tasks", json={"title": "Task", "status": "bogus", "priority": "medium"})
    assert response.status_code == 422


def test_create_task_missing_priority_returns_422(client):
    response = client.post("/tasks", json={"title": "Task"})
    assert response.status_code == 422


def test_create_task_invalid_priority_returns_422(client):
    response = client.post("/tasks", json={"title": "Task", "priority": "urgent"})
    assert response.status_code == 422


def test_list_returns_created_tasks(client):
    client.post("/tasks", json={"title": "First", "priority": "low"})
    client.post("/tasks", json={"title": "Second", "priority": "high"})

    response = client.get("/tasks")
    assert response.status_code == 200
    titles = [task["title"] for task in response.json()]
    assert titles == ["First", "Second"]
