def test_health_and_json_errors(client):
    assert client.get("/health").json["status"] == "ok"
    response = client.get("/missing")
    assert response.status_code == 404
    assert response.json["error"]["code"] == 404
    wrong_method = client.get("/api/v1/analyze")
    assert wrong_method.status_code == 405
    assert "POST" in wrong_method.headers["Allow"]
