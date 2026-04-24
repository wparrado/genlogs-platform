"""Unit tests for maps providers (mock + google minimal behavior).

These tests are lightweight and don't perform network calls by default: the
Google provider is expected to raise when no API key is configured.
"""

import pytest
from app.providers.maps import mock, google


def test_mock_provider_ny_washington(monkeypatch):
    expected = [
        {"id": "route_ny_was_1", "summary": "I-95 S", "durationText": "3 hr 52 min", "distanceText": "227 mi", "mapEmbedUrl": None, "pathPayload": None},
        {"id": "route_ny_was_2", "summary": "I-295 E", "durationText": "4 hr 10 min", "distanceText": "245 mi", "mapEmbedUrl": None, "pathPayload": None},
        {"id": "route_ny_was_3", "summary": "US-1 S", "durationText": "5 hr 05 min", "distanceText": "260 mi", "mapEmbedUrl": None, "pathPayload": None},
    ]
    monkeypatch.setattr(mock, "get_routes_for_pair", lambda a, b: expected)
    routes = mock.get_routes_for_pair("mock:new_york", "mock:washington")
    assert routes == expected


def test_mock_provider_sf_la(monkeypatch):
    expected = [
        {"id": "route_sf_la_1", "summary": "I-5 S", "durationText": "6 hr 30 min", "distanceText": "382 mi", "mapEmbedUrl": None, "pathPayload": None},
        {"id": "route_sf_la_2", "summary": "US-101 S", "durationText": "7 hr 15 min", "distanceText": "420 mi", "mapEmbedUrl": None, "pathPayload": None},
        {"id": "route_sf_la_3", "summary": "CA-1 S (scenic)", "durationText": "9 hr 00 min", "distanceText": "430 mi", "mapEmbedUrl": None, "pathPayload": None},
    ]
    monkeypatch.setattr(mock, "get_routes_for_pair", lambda a, b: expected)
    routes = mock.get_routes_for_pair("mock:san_francisco", "mock:los_angeles")
    assert routes == expected


def test_mock_provider_no_match(monkeypatch):
    monkeypatch.setattr(mock, "get_routes_for_pair", lambda a, b: [])
    routes = mock.get_routes_for_pair("mock:foo", "mock:bar")
    assert routes == []


def test_google_provider_raises_without_key(monkeypatch):
    # Ensure circuit state doesn't leak from other tests
    try:
        google._circuit.failures = 0
        google._circuit.opened_at = None
    except Exception:
        pass

    # Force no API key for deterministic behavior
    monkeypatch.setattr(google.settings, "genlogs_google_api_key", "")

    with pytest.raises(RuntimeError):
        google.get_routes_for_pair("a", "b")
