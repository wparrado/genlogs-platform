from sqlmodel import Session, create_engine

import app.providers.db.db as db_mod
from app.providers.db.models import CityReference, Carrier, CarrierRoute


def _setup_in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    # replace provider engine with in-memory engine for testing
    db_mod.engine = engine
    db_mod.init_db()
    return engine


def test_suggest_cities_returns_matches():
    engine = _setup_in_memory_db()
    with Session(engine) as session:
        ny = CityReference(place_id="mock:new_york", name="New York", state="NY", country="US", normalized_label="new york, ny, us")
        la = CityReference(place_id="mock:los_angeles", name="Los Angeles", state="CA", country="US", normalized_label="los angeles, ca, us")
        session.add_all([ny, la])
        session.commit()

    items = db_mod.suggest_cities("New", limit=10)
    assert any("New York" in it["label"] for it in items)


def test_get_carriers_for_pair_specific_and_generic():
    engine = _setup_in_memory_db()
    with Session(engine) as session:
        ny = CityReference(place_id="mock:new_york", name="New York", state="NY", country="US", normalized_label="new york, ny, us")
        was = CityReference(place_id="mock:washington", name="Washington", state="DC", country="US", normalized_label="washington, dc, us")
        session.add_all([ny, was])
        session.commit()

        knight = Carrier(name="Knight-Swift Transport Services")
        ups = Carrier(name="UPS Inc.")
        session.add_all([knight, ups])
        session.commit()

        r1 = CarrierRoute(origin_city_id=ny.id, destination_city_id=was.id, carrier_id=knight.id, daily_trucks=10)
        r2 = CarrierRoute(origin_city_id=None, destination_city_id=None, carrier_id=ups.id, daily_trucks=5)
        session.add_all([r1, r2])
        session.commit()

    carriers = db_mod.get_carriers_for_pair("mock:new_york", "mock:washington")
    assert carriers and carriers[0]["name"] == "Knight-Swift Transport Services"

    generic = db_mod.get_carriers_for_pair("mock:unknown", "mock:unknown")
    assert any(c["name"] == "UPS Inc." for c in generic)
