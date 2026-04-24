import app.providers.maps.google_places as gp
from app.services.city_service import suggest_cities
import app.config.settings as cfg


def test_suggest_cities_uses_google_when_configured(monkeypatch):
    expected = [{"id": "p1", "label": "New York, NY, US", "city": "New York", "state": "NY", "country": "US"}]
    monkeypatch.setattr(gp, "get_city_suggestions", lambda q, limit=10: expected)
    # set provider to google
    monkeypatch.setattr(cfg.settings, "genlogs_maps_provider", "google", raising=False)

    res = suggest_cities("New", limit=5)
    assert res == expected


def test_suggest_cities_falls_back_to_db_when_google_fails(monkeypatch):
    # simulate google raising
    monkeypatch.setattr(gp, "get_city_suggestions", lambda q, limit=10: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(cfg.settings, "genlogs_maps_provider", "google", raising=False)

    # monkeypatch db provider to return known result
    from app.providers import db as dbp
    monkeypatch.setattr(dbp, "suggest_cities", lambda q, limit=10: [{"id":"d1","label":"DB City","city":"DB City","state":"","country":"US"}])

    res = suggest_cities("Xyz", limit=5)
    assert isinstance(res, list)
    assert res[0]["label"] == "DB City"
