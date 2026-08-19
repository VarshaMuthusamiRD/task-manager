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


def test_empty_string_api_key_header_returns_401(client):
    client.headers["X-API-Key"] = ""
    response = client.get("/tasks")
    assert response.status_code == 401


def test_api_key_is_case_sensitive(client):
    client.headers["X-API-Key"] = client.headers["X-API-Key"].upper()
    response = client.get("/tasks")
    assert response.status_code == 401


def test_server_without_api_key_configured_returns_500(client_no_server_key):
    response = client_no_server_key.get("/tasks")
    assert response.status_code == 500
    assert "API_KEY" in response.json()["detail"]
