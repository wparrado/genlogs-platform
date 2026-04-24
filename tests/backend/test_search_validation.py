import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _call_search(client, payload):
    params = {}
    f = payload.get("from")
    t = payload.get("to")
    if isinstance(f, dict):
        params["from_id"] = f.get("id")
    elif f is not None:
        params["from_id"] = str(f)
    if isinstance(t, dict):
        params["to_id"] = t.get("id")
    elif t is not None:
        params["to_id"] = str(t)
    return client.get("/api/search", params=params)


def _error_shape(obj: dict) -> None:
    assert isinstance(obj, dict)
    assert "code" in obj
    assert "message" in obj


def test_missing_from_rejected() -> None:
    """Reject requests with a missing `from` city (400 and stable error shape)."""
    payload = {"to": {"id": "place_was", "label": "Washington, DC, USA", "city": "Washington", "state": "DC", "country": "US"}}
    resp = _call_search(client, payload)
    assert resp.status_code == 400
    _error_shape(resp.json())


def test_missing_to_rejected() -> None:
    """Reject requests with a missing `to` city (400 and stable error shape)."""
    payload = {"from": {"id": "place_nyc", "label": "New York, NY, USA", "city": "New York", "state": "NY", "country": "US"}}
    resp = _call_search(client, payload)
    assert resp.status_code == 400
    _error_shape(resp.json())


def test_whitespace_only_input_rejected() -> None:
    """Reject whitespace-only inputs for city selection."""
    payload = {
        "from": {"id": "", "label": "   ", "city": "", "state": "", "country": ""},
        "to": {"id": "place_was", "label": "Washington, DC, USA", "city": "Washington", "state": "DC", "country": "US"},
    }
    resp = _call_search(client, payload)
    assert resp.status_code == 400
    _error_shape(resp.json())


def test_same_city_rejected() -> None:
    """Reject requests where `from` and `to` are the same canonical city (400).

    The canonical equality is based on the `id` field in the contract.
    """
    city = {"id": "place_nyc", "label": "New York, NY, USA", "city": "New York", "state": "NY", "country": "US"}
    payload = {"from": city, "to": city}
    resp = _call_search(client, payload)
    assert resp.status_code == 400
    _error_shape(resp.json())


def test_malformed_payload_rejected() -> None:
    """Reject malformed payloads with a stable error shape (400).

    Send values that do not match the SearchRequest schema.
    """
    payload = {"from": "not-an-object", "to": 123}
    resp = _call_search(client, payload)
    assert resp.status_code == 400
    _error_shape(resp.json())
