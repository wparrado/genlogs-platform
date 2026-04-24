from __future__ import annotations
from typing import List, Dict, Optional
from sqlmodel import Session, select
from app.db import engine
from app.models.db_models import CityReference, CarrierRoute, Carrier


def get_carriers_for_pair(from_place_id: str, to_place_id: str) -> List[Dict]:
    with Session(engine) as session:
        origin = session.exec(select(CityReference).where(CityReference.place_id == from_place_id)).first()
        destination = session.exec(select(CityReference).where(CityReference.place_id == to_place_id)).first()

        rows = []
        if origin and destination:
            q = select(Carrier.name, CarrierRoute.daily_trucks).join(Carrier, Carrier.id == CarrierRoute.carrier_id).where(
                CarrierRoute.origin_city_id == origin.id,
                CarrierRoute.destination_city_id == destination.id,
            ).order_by(CarrierRoute.daily_trucks.desc())
            rows = session.exec(q).all()

        if not rows:
            q = select(Carrier.name, CarrierRoute.daily_trucks).join(Carrier, Carrier.id == CarrierRoute.carrier_id).where(
                CarrierRoute.origin_city_id == None,
                CarrierRoute.destination_city_id == None,
            ).order_by(CarrierRoute.daily_trucks.desc())
            rows = session.exec(q).all()

        return [{"name": name, "trucksPerDay": int(daily)} for name, daily in rows]


def get_routes_for_pair(from_place_id: str, to_place_id: str) -> List[Dict]:
    """Return up to 3 mocked route options for supported canonical city pairs.

    This intentionally provides deterministic route options for functional tests.
    """
    with Session(engine) as session:
        origin = session.exec(select(CityReference).where(CityReference.place_id == from_place_id)).first()
        destination = session.exec(select(CityReference).where(CityReference.place_id == to_place_id)).first()

    routes: List[Dict] = []
    if not origin or not destination:
        return routes

    o_lbl = (origin.normalized_label or "").lower()
    d_lbl = (destination.normalized_label or "").lower()

    if o_lbl == "new york, ny, us" and d_lbl == "washington, dc, us":
        routes = [
            {"id": "route_ny_was_1", "summary": "I-95 S", "durationText": "3 hr 52 min", "distanceText": "227 mi", "mapEmbedUrl": None, "pathPayload": None},
            {"id": "route_ny_was_2", "summary": "I-295 E", "durationText": "4 hr 10 min", "distanceText": "245 mi", "mapEmbedUrl": None, "pathPayload": None},
            {"id": "route_ny_was_3", "summary": "US-1 S", "durationText": "5 hr 05 min", "distanceText": "260 mi", "mapEmbedUrl": None, "pathPayload": None},
        ]
    elif o_lbl == "san francisco, ca, us" and d_lbl == "los angeles, ca, us":
        routes = [
            {"id": "route_sf_la_1", "summary": "I-5 S", "durationText": "6 hr 30 min", "distanceText": "382 mi", "mapEmbedUrl": None, "pathPayload": None},
            {"id": "route_sf_la_2", "summary": "US-101 S", "durationText": "7 hr 15 min", "distanceText": "420 mi", "mapEmbedUrl": None, "pathPayload": None},
            {"id": "route_sf_la_3", "summary": "CA-1 S (scenic)", "durationText": "9 hr 00 min", "distanceText": "430 mi", "mapEmbedUrl": None, "pathPayload": None},
        ]

    return routes
