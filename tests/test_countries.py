import json

import pytest

from backend_lab import create_app
from backend_lab.countries import load_countries

URL = "/api/v1/countries"


def test_filter_sort_and_limit(client):
    data = client.get(URL, query_string={"language": "ENGLISH", "sort": "population", "limit": 2}).json
    assert data["dataset"] == "fictional-demo"
    assert data["total"] == 3
    assert [row["name"] for row in data["items"]] == ["Northvale", "Cedar Republic"]
    assert client.get(URL, query_string={"name": "harbor"}).json["total"] == 1


def test_aggregates_count_countries_not_speakers(client):
    data = client.get(URL + "/stats", query_string={"top_n": 2}).json
    assert data["country_count"] == 6
    assert data["total_population"] == 8950000
    assert data["top_languages"] == [{"language": "english", "country_count": 3},
                                     {"language": "spanish", "country_count": 3}]
    filtered = client.get(URL + "/stats", query_string={"language": "Portuguese"}).json
    assert filtered["country_count"] == 2
    assert filtered["total_population"] == 2300000
    empty = client.get(URL + "/stats", query_string={"name": "missing"}).json
    assert empty["country_count"] == 0
    assert empty["total_population"] == 0
    assert empty["top_languages"] == []


@pytest.mark.parametrize("path", ["?sort=wrong", "?limit=0", "?limit=251", "/stats?top_n=wrong", "?unknown=1"])
def test_invalid_query(client, path):
    assert client.get(URL + path).status_code == 400


def test_custom_dataset_normalizes_labels(tmp_path):
    path = tmp_path / "countries.json"
    path.write_text(json.dumps([{"name": "Test", "population": 12, "languages": ["English", "english", " English "]}]))
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "data.sqlite3"), "COUNTRIES_FILE": str(path)})
    data = app.test_client().get(URL + "/stats").json
    assert data["dataset"] == "custom"
    assert data["top_languages"] == [{"language": "english", "country_count": 1}]


@pytest.mark.parametrize("rows", [[], {}, [1], [{"name": "X", "population": True, "languages": ["English"]}],
                                   [{"name": "X", "population": 1, "languages": []}],
                                   [{"name": "X", "population": -1, "languages": ["English"]}],
                                   [{"name": "X", "population": 1, "languages": [1]}],
                                   [{"name": "X", "population": 1, "languages": ["English"]}] * 2])
def test_invalid_dataset_fails_at_startup(tmp_path, rows):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(rows))
    with pytest.raises(ValueError):
        load_countries(path)
