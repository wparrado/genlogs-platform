import pytest
import app.providers.maps.google as google
from app.metrics import reset, get


def test_google_returns_empty_routes_when_payload_empty(monkeypatch):
    monkeypatch.setattr(google.settings, "genlogs_google_api_key", "fake-key")
    monkeypatch.setattr(google, "_call_google_directions", lambda a, b, k: {"routes": []})
    reset()
    routes = google.get_routes_for_pair("a", "b")
    assert routes == []
    assert get("maps_google_attempts") >= 1


def test_google_partial_legs_parsed(monkeypatch):
    monkeypatch.setattr(google.settings, "genlogs_google_api_key", "fake-key")
    payload = {"routes": [{"summary": "R1", "legs": [{}]}]}
    monkeypatch.setattr(google, "_call_google_directions", lambda a, b, k: payload)
    reset()
    routes = google.get_routes_for_pair("a", "b")
    assert routes[0]["summary"] == "R1"
    assert routes[0]["durationText"] == ""


def test_metrics_increment_on_failure(monkeypatch):
    monkeypatch.setattr(google.settings, "genlogs_google_api_key", "fake-key")
    def bad(a, b, k):
        raise Exception("boom")
    monkeypatch.setattr(google, "_call_google_directions", bad)
    reset()
    with pytest.raises(Exception):
        google.get_routes_for_pair("a", "b")
    assert get("maps_google_failures") >= 1
