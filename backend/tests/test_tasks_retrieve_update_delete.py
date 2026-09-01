def _create(client, title="Task", priority="medium"):
    response = client.post("/tasks", json={"title": title, "priority": priority})
    return response.json()


def test_get_task_happy_path(client):
    created = _create(client)
    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_task_missing_id_returns_404(client):
    response = client.get("/tasks/999")
    assert response.status_code == 404


def test_update_task_happy_path(client):
    created = _create(client, priority="low")
    payload = {"title": "Updated", "description": "new desc", "status": "done", "priority": "high"}
    response = client.put(f"/tasks/{created['id']}", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Updated"
    assert body["status"] == "done"
    assert body["priority"] == "high"
    assert body["created_at"] == created["created_at"]
    assert body["updated_at"] != created["updated_at"]


def test_update_task_missing_id_returns_404(client):
    response = client.put("/tasks/999", json={"title": "X", "priority": "medium"})
    assert response.status_code == 404


def test_update_task_invalid_payload_returns_422(client):
    created = _create(client)
    response = client.put(f"/tasks/{created['id']}", json={"title": "", "priority": "medium"})
    assert response.status_code == 422


def test_update_task_missing_priority_returns_422(client):
    created = _create(client)
    response = client.put(f"/tasks/{created['id']}", json={"title": "Task"})
    assert response.status_code == 422


def test_update_task_invalid_priority_returns_422(client):
    created = _create(client)
    response = client.put(f"/tasks/{created['id']}", json={"title": "Task", "priority": "urgent"})
    assert response.status_code == 422


def test_delete_task_happy_path(client):
    created = _create(client)
    response = client.delete(f"/tasks/{created['id']}")
    assert response.status_code == 204

    follow_up = client.get(f"/tasks/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_task_missing_id_returns_404(client):
    response = client.delete("/tasks/999")
    assert response.status_code == 404
