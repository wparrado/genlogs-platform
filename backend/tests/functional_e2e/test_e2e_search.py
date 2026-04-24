import requests

BASE = "http://127.0.0.1:8001"


def _make_city(place_id, name, state, country='US'):
    return {"id": place_id, "label": f"{name}, {state}, {country}", "city": name, "state": state, "country": country}


def test_health():
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_ny_to_washington_e2e():
    from_city = _make_city("mock:new_york", "New York", "NY")
    to_city = _make_city("mock:washington", "Washington", "DC")
    r = requests.get(f"{BASE}/api/search", params={"from_id": from_city["id"], "to_id": to_city["id"]})
    assert r.status_code == 200
    data = r.json()
    assert len(data.get("routes", [])) == 3
    assert len(data.get("carriers", [])) >= 3


def test_cities_suggestion_e2e():
    r = requests.get(f"{BASE}/api/cities?query=New")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
