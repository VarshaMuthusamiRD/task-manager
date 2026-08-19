def test_localhost_origin_is_allowed(client):
    response = client.get("/tasks", headers={"Origin": "http://localhost:5173"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_127_0_0_1_origin_is_allowed(client):
    response = client.get("/tasks", headers={"Origin": "http://127.0.0.1:5173"})
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_unrelated_origin_is_not_allowed(client):
    response = client.get("/tasks", headers={"Origin": "http://evil.example.com"})
    assert "access-control-allow-origin" not in response.headers
