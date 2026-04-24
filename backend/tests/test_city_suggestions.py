from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _error_shape(obj: dict) -> None:
    assert isinstance(obj, dict)
    assert "code" in obj
    assert "message" in obj


def test_rejects_empty_or_too_short_query() -> None:
    # Too short
    resp = client.get("/api/cities?query=a")
    assert resp.status_code == 400
    _error_shape(resp.json())

    # Missing
    resp2 = client.get("/api/cities")
    assert resp2.status_code == 400
    _error_shape(resp2.json())


def test_trims_and_normalizes_query_whitespace() -> None:
    resp = client.get("/api/cities?query=  New  ")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "items" in data
    assert isinstance(data["items"], list)


def test_returns_normalized_suggestions_for_valid_query() -> None:
    resp = client.get("/api/cities?query=New")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "items" in data
    assert isinstance(data["items"], list)


def test_returns_empty_list_for_no_matches() -> None:
    resp = client.get("/api/cities?query=NoSuchCityNameShouldReturnEmpty")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["items"] == []
