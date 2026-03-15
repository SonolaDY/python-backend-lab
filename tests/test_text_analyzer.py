import pytest


def test_unicode_case_and_apostrophes(client):
    text = "Hello, HELLO! Café café. Don't don’t 123."
    response = client.post("/api/v1/analyze", json={"text": text, "top_n": 2})
    assert response.status_code == 200
    assert response.json == {
        "character_count": len(text), "word_count": 6, "unique_word_count": 3,
        "top_words": [{"word": "café", "count": 2}, {"word": "don't", "count": 2}],
    }


def test_empty_text_is_valid(client):
    data = client.post("/api/v1/analyze", json={"text": ""}).json
    assert data == {"character_count": 0, "word_count": 0, "unique_word_count": 0, "top_words": []}


@pytest.mark.parametrize("data", [{}, [], {"text": 123}, {"text": "x", "top_n": True},
                                  {"text": "x", "top_n": 0}, {"text": "x", "top_n": 51},
                                  {"text": "x" * 50001}, {"text": "ok", "extra": 1}])
def test_invalid_input(client, data):
    response = client.post("/api/v1/analyze", json=data)
    assert response.status_code == 400
    assert response.json["error"]["code"] == 400


def test_bad_json_media_type_and_size(client):
    assert client.post("/api/v1/analyze", data="{", content_type="application/json").status_code == 400
    assert client.post("/api/v1/analyze", data="plain text").status_code == 415
    response = client.post("/api/v1/analyze", json={"text": "x" * 140000})
    assert response.status_code == 413
    assert response.is_json
