from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _make_city(place_id, name, state, country='US'):
    return {"id": place_id, "label": f"{name}, {state}, {country}", "city": name, "state": state, "country": country}


def test_ny_to_washington_shows_carriers_and_routes():
    from_city = _make_city("mock:new_york", "New York", "NY")
    to_city = _make_city("mock:washington", "Washington", "DC")
    resp = client.get("/api/search", params={"from_id": from_city["id"], "to_id": to_city["id"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "carriers" in data and isinstance(data["carriers"], list)
    assert len(data["carriers"]) >= 3
    assert data["carriers"][0]["name"].startswith("Knight-Swift")
    assert "routes" in data and len(data["routes"]) == 3


def test_sf_to_la_shows_carriers_and_routes():
    from_city = _make_city("mock:san_francisco", "San Francisco", "CA")
    to_city = _make_city("mock:los_angeles", "Los Angeles", "CA")
    resp = client.get("/api/search", params={"from_id": from_city["id"], "to_id": to_city["id"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["carriers"][0]["name"].startswith("XPO")
    assert len(data["routes"]) == 3


def test_generic_fallback_applies_for_other_pairs():
    # Use NY -> Los Angeles (no specific rule seeded) so generic fallback applies
    from_city = _make_city("mock:new_york", "New York", "NY")
    to_city = _make_city("mock:los_angeles", "Los Angeles", "CA")
    resp = client.get("/api/search", params={"from_id": from_city["id"], "to_id": to_city["id"]})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["carriers"]) >= 2
    assert data["carriers"][0]["name"] == "UPS Inc." or data["carriers"][0]["name"] == "UPS Inc."
