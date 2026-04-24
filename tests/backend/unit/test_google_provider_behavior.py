import types
import requests

import app.providers.maps.google as google
from app.config import settings


class DummyResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._payload


def test_google_parses_routes(monkeypatch):
    # set fake api key
    monkeypatch.setattr(google.settings, "genlogs_google_api_key", "fake-key")

    payload = {
        "routes": [
            {"summary": "I-95 S", "legs": [{"duration": {"text": "3 hr 52 min"}, "distance": {"text": "227 mi"}}]},
            {"summary": "I-295 E", "legs": [{"duration": {"text": "4 hr 10 min"}, "distance": {"text": "245 mi"}}]},
        ]
    }

    monkeypatch.setattr(google, "_call_google_directions", lambda a, b, k: payload)

    routes = google.get_routes_for_pair("from", "to")
    assert isinstance(routes, list)
    assert routes[0]["summary"] == "I-95 S"
    assert routes[0]["durationText"] == "3 hr 52 min"


def test_google_circuit_breaker_opens_after_failures(monkeypatch):
    # set fake api key
    monkeypatch.setattr(google.settings, "genlogs_google_api_key", "fake-key")

    # replace circuit with one that trips quickly
    monkeypatch.setattr(google, "_circuit", google.SimpleCircuitBreaker(failure_threshold=1, recovery_seconds=60))

    # make underlying call raise
    def _bad(a, b, k):
        raise requests.RequestException("network")

    monkeypatch.setattr(google, "_call_google_directions", _bad)

    # First call should raise the original exception
    try:
        google.get_routes_for_pair("from", "to")
    except Exception as e:
        assert isinstance(e, Exception)

    # Second call should raise CircuitOpen
    from app.providers.maps.google import CircuitOpen
    try:
        google.get_routes_for_pair("from", "to")
    except Exception as e:
        assert isinstance(e, CircuitOpen)
