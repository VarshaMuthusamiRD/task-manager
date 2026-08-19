def test_request_without_api_key_returns_401(client):
    client.headers.pop("X-API-Key")
    response = client.get("/tasks")
    assert response.status_code == 401


def test_request_with_wrong_api_key_returns_401(client):
    client.headers["X-API-Key"] = "wrong-key"
    response = client.get("/tasks")
    assert response.status_code == 401


def test_request_with_correct_api_key_succeeds(client):
    response = client.get("/tasks")
    assert response.status_code == 200
