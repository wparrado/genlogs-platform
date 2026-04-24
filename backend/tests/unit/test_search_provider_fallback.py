"""Test that search_service falls back to mock when google provider fails."""

from app.services.search_service import get_routes_for_pair
import app.providers.maps.google as google_provider
import app.providers.maps.mock as mock_provider


def test_fallback_to_mock(monkeypatch):
    # simulate google provider raising
    monkeypatch.setattr(google_provider, "get_routes_for_pair", lambda a, b: (_ for _ in ()).throw(RuntimeError("simulated failure")))

    # simulate mock provider returning deterministic routes without touching DB
    expected = [
        {"id": "route_ny_was_1", "summary": "I-95 S", "durationText": "3 hr 52 min", "distanceText": "227 mi", "mapEmbedUrl": None, "pathPayload": None},
        {"id": "route_ny_was_2", "summary": "I-295 E", "durationText": "4 hr 10 min", "distanceText": "245 mi", "mapEmbedUrl": None, "pathPayload": None},
        {"id": "route_ny_was_3", "summary": "US-1 S", "durationText": "5 hr 05 min", "distanceText": "260 mi", "mapEmbedUrl": None, "pathPayload": None},
    ]
    monkeypatch.setattr(mock_provider, "get_routes_for_pair", lambda a, b: expected)

    routes = get_routes_for_pair("mock:new_york", "mock:washington")
    assert routes == expected
