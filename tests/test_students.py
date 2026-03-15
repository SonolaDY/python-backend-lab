import pytest

from backend_lab import create_app

URL = "/api/v1/students"


def test_full_lifecycle_and_persistence(client, app):
    created = client.post(URL, json={"name": " Ada Example ", "country": "Demo", "skills": ["SQL", "SQL"]})
    assert created.status_code == 201
    path = created.headers["Location"]
    assert created.json["name"] == "Ada Example"
    assert created.json["skills"] == ["SQL"]
    assert client.get(path).json == created.json
    updated = client.patch(path, json={"skills": ["SQL", "Python"], "birth_year": 1998})
    assert updated.status_code == 200
    assert updated.json["name"] == "Ada Example"
    assert updated.json["skills"] == ["SQL", "Python"]
    assert updated.json["created_at"] == created.json["created_at"]
    restarted = create_app({"TESTING": True, "DATABASE": app.config["DATABASE"], "COUNTRIES_FILE": None})
    assert restarted.test_client().get(path).json == updated.json
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404
    assert client.delete(path).status_code == 404


def test_pagination_filtering_and_sql_values(client):
    for name, country in [("A", "Demo"), ("B", "Demo"), ("C", "Elsewhere"), ("D", "x' OR 1=1 --")]:
        assert client.post(URL, json={"name": name, "country": country}).status_code == 201
    page = client.get(URL, query_string={"country": "demo", "per_page": 1, "page": 2}).json
    assert page["total"] == 2
    assert [row["name"] for row in page["items"]] == ["B"]
    injected = client.get(URL, query_string={"country": "x' OR 1=1 --"}).json
    assert injected["total"] == 1
    assert injected["items"][0]["name"] == "D"
    assert client.get(URL, query_string={"page": 20}).json["items"] == []


@pytest.mark.parametrize("data", [{}, {"country": "Demo"}, {"name": " "}, {"name": 1},
                                  {"name": "A", "birth_year": True}, {"name": "A", "birth_year": 1800},
                                  {"name": "A", "skills": "SQL"}, {"name": "A", "skills": [""]},
                                  {"name": "A", "id": 123}, {"name": "A", "bio": "x" * 2001}])
def test_invalid_creation_leaves_database_empty(client, data):
    assert client.post(URL, json=data).status_code == 400
    assert client.get(URL).json["total"] == 0


def test_invalid_patch_is_atomic(client):
    created = client.post(URL, json={"name": "Original"})
    path = created.headers["Location"]
    assert client.patch(path, json={"name": "Changed", "birth_year": "wrong"}).status_code == 400
    assert client.get(path).json == created.json
    assert client.patch(path, json={}).status_code == 400
    assert client.patch("/api/v1/students/999", json={"name": "Unknown"}).status_code == 404


@pytest.mark.parametrize("query", [{"page": "0"}, {"page": "x"}, {"per_page": "101"},
                                   {"page": "9" * 100}, {"page": "²"}, {"unknown": "x"},
                                   [("page", "1"), ("page", "2")]])
def test_invalid_query(client, query):
    assert client.get(URL, query_string=query).status_code == 400


def test_out_of_range_id_returns_not_found(client):
    path = URL + "/" + str(2**64)
    assert client.get(path).status_code == 404
    assert client.patch(path, json={"name": "Unknown"}).status_code == 404
    assert client.delete(path).status_code == 404
