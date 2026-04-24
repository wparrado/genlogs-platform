from sqlmodel import Session, select
from app.providers.db import engine, CityReference, Carrier, CarrierRoute
import uuid
import os
import requests
import logging

logger = logging.getLogger(__name__)

# Minimal id lookup by name helper


from typing import Optional

def _find_place_id_via_google(query_text: str, api_key: str) -> Optional[str]:
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": query_text,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": api_key,
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        payload = r.json()
        cand = payload.get("candidates", [])
        if cand:
            return cand[0].get("place_id")
    except Exception as exc:
        logger.debug("Google Find Place failed for %s: %s", query_text, exc)
    return None


def get_or_create_city(session: Session, name, state, country='US', place_id=None, normalized_label=None):
    norm = (normalized_label or f"{name}, {state}, {country}").lower()
    existing = session.exec(select(CityReference).where(CityReference.normalized_label == norm)).first()
    if existing:
        # If existing row has no place_id but we were given one, attach it
        if place_id and not existing.place_id:
            existing.place_id = place_id
            session.add(existing)
            session.commit()
            session.refresh(existing)
        return existing

    # If no explicit place_id provided, and a Google API key is configured,
    # attempt to resolve the place_id via Find Place so seeded cities match Google ids.
    if not place_id:
        api_key = os.environ.get("GENLOGS_GOOGLE_API_KEY")
        if api_key:
            query_text = f"{name}, {state}, {country}"
            pid = _find_place_id_via_google(query_text, api_key)
            if pid:
                place_id = pid

    c = CityReference(place_id=place_id or f"mock:{name.lower().replace(' ','_')}", name=name, state=state, country=country, normalized_label=norm)
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


def get_or_create_carrier(session: Session, name):
    existing = session.exec(select(Carrier).where(Carrier.name == name)).first()
    if existing:
        return existing
    c = Carrier(name=name)
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


def seed():
    with Session(engine) as session:
        # cities
        ny = get_or_create_city(session, 'New York', 'NY')
        was = get_or_create_city(session, 'Washington', 'DC')
        sf = get_or_create_city(session, 'San Francisco', 'CA')
        la = get_or_create_city(session, 'Los Angeles', 'CA')

        # carriers
        knight = get_or_create_carrier(session, 'Knight-Swift Transport Services')
        jb = get_or_create_carrier(session, 'J.B. Hunt Transport Services Inc')
        yrc = get_or_create_carrier(session, 'YRC Worldwide')
        xpo = get_or_create_carrier(session, 'XPO Logistics')
        sch = get_or_create_carrier(session, 'Schneider')
        land = get_or_create_carrier(session, 'Landstar Systems')
        ups = get_or_create_carrier(session, 'UPS Inc.')
        fed = get_or_create_carrier(session, 'FedEx Corp')

        # carrier routes (specific)
        def create_route(o, d, carrier, daily):
            existing = session.exec(select(CarrierRoute).where(CarrierRoute.origin_city_id == o.id, CarrierRoute.destination_city_id == d.id, CarrierRoute.carrier_id == carrier.id)).first()
            if existing:
                return existing
            r = CarrierRoute(origin_city_id=o.id, destination_city_id=d.id, carrier_id=carrier.id, daily_trucks=daily)
            session.add(r)
            session.commit()
            session.refresh(r)
            return r

        create_route(ny, was, knight, 10)
        create_route(ny, was, jb, 7)
        create_route(ny, was, yrc, 5)

        create_route(sf, la, xpo, 9)
        create_route(sf, la, sch, 6)
        create_route(sf, la, land, 2)

        # generic defaults (origin NULL, destination NULL)
        existing_generic = session.exec(select(CarrierRoute).where(CarrierRoute.origin_city_id == None, CarrierRoute.destination_city_id == None)).all()
        if not existing_generic:
            r1 = CarrierRoute(origin_city_id=None, destination_city_id=None, carrier_id=ups.id, daily_trucks=11)
            r2 = CarrierRoute(origin_city_id=None, destination_city_id=None, carrier_id=fed.id, daily_trucks=9)
            session.add_all([r1, r2])
            session.commit()


if __name__ == '__main__':
    seed()
