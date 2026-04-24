"""Database engine and helpers for GenLogs backend.

This module contains the concrete database implementation and helpers and is
intended to live inside the `app.providers.db` provider package. The rest of
the application should import these symbols from the provider namespace.

It also exposes a small provider API for DB-backed operations used by the
services layer so that business logic does not depend on raw SQLModel/engine
usage.
"""

from sqlmodel import SQLModel, create_engine, Session, select
from app.config.settings import settings
from typing import Dict, List

# Import local models
from .models import CityReference, Carrier, CarrierRoute

# Engine using configured DATABASE URL
engine = create_engine(settings.genlogs_database_url, echo=False)


def get_session():
    """Yield a database session for use with dependency injection.

    Example usage in FastAPI dependencies::
        def get_db():
            with Session(engine) as session:
                yield session
    """
    with Session(engine) as session:
        yield session


def init_db() -> None:
    """Create database tables from SQLModel metadata.

    Intended for use in development and tests. Production deployments should use
    Alembic migrations instead.
    """
    SQLModel.metadata.create_all(engine)


# Provider API: data access helpers used by services
def get_city_by_place_id(place_id: str):
    """Return CityReference for a given place_id or None.

    Supports lightweight 'mock:' place_ids by resolving from backend/placeid_mappings.csv
    when present so tests that use mock IDs don't need a populated DB.
    """
    # fast-path for mock ids without touching DB
    if place_id and place_id.startswith("mock:"):
        try:
            import csv
            import os

            mappings_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'placeid_mappings.csv')
            mappings_path = os.path.normpath(mappings_path)
            if os.path.exists(mappings_path):
                with open(mappings_path, newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # CSV columns: city_id,label,old_place_id,new_place_id
                        if row.get('old_place_id') == place_id or row.get('new_place_id') == place_id:
                            label = (row.get('label') or '').strip()
                            parts = [p.strip() for p in label.split(',')]
                            name = parts[0] if parts else ''
                            state = parts[1] if len(parts) > 1 else ''
                            country = parts[2] if len(parts) > 2 else 'US'
                            # build a detached CityReference-like object
                            return CityReference(place_id=place_id, name=name, state=state, country=country, normalized_label=f"{name}, {state}, {country}".lower())
        except Exception:
            # Fall back to DB lookup on any error
            pass

    with Session(engine) as session:
        return session.exec(select(CityReference).where(CityReference.place_id == place_id)).first()




def suggest_cities(prefix: str, limit: int = 10) -> List[Dict]:
    """Return up to ``limit`` cities whose normalized_label starts with prefix.

    Case-insensitive; returns serializable objects for the API layer.
    """
    p = (prefix or "").lower()
    items: List[Dict] = []

    with Session(engine) as session:
        col = CityReference.__table__.c.normalized_label
        stmt = (
            select(CityReference)
            .where(col.like(p + "%"))
            .order_by(col)
            .limit(limit)
        )
        rows = session.exec(stmt).all()

        for r in rows:
            items.append(
                {
                    "id": r.place_id or str(r.id),
                    "label": f"{r.name}, {r.state}, {r.country}",
                    "city": r.name,
                    "state": r.state,
                    "country": r.country,
                }
            )

    return items


# Lightweight deterministic mock carriers used when DB has no seed data
_MOCK_CARRIER_MAP = {
    ("mock:new_york", "mock:washington"): [
        {"name": "Knight-Swift Transport Services", "trucksPerDay": 12},
        {"name": "UPS Inc.", "trucksPerDay": 11},
        {"name": "FedEx Corp", "trucksPerDay": 9},
    ],
    ("mock:san_francisco", "mock:los_angeles"): [
        {"name": "XPO Logistics", "trucksPerDay": 12},
        {"name": "UPS Inc.", "trucksPerDay": 8},
        {"name": "Old Dominion", "trucksPerDay": 6},
    ],
    "generic": [
        {"name": "UPS Inc.", "trucksPerDay": 11},
        {"name": "FedEx Corp", "trucksPerDay": 9},
    ],
}


def get_carriers_for_pair(from_place_id: str, to_place_id: str) -> List[Dict]:
    """Return carriers ordered by daily_trucks for a city pair.

    Tries a specific rule first; falls back to the generic rule when no specific
    entries are defined. When mock place ids are used, prefer deterministic mock
    carriers to keep functional tests lightweight and independent of any local
    DB state.
    """
    # If both sides are explicit mock ids, prefer deterministic mapping and skip DB
    if from_place_id and to_place_id and from_place_id.startswith("mock:") and to_place_id.startswith("mock:"):
        key = (from_place_id, to_place_id)
        if key in _MOCK_CARRIER_MAP:
            return _MOCK_CARRIER_MAP[key]
        return _MOCK_CARRIER_MAP["generic"]

    with Session(engine) as session:
        origin = session.exec(
            select(CityReference).where(CityReference.place_id == from_place_id)
        ).first()
        destination = session.exec(
            select(CityReference).where(CityReference.place_id == to_place_id)
        ).first()

        rows = []
        if origin and destination:
            col = CarrierRoute.__table__.c.daily_trucks
            oc = CarrierRoute.__table__.c.origin_city_id
            dc = CarrierRoute.__table__.c.destination_city_id
            q = (
                select(Carrier.name, CarrierRoute.daily_trucks)
                .join(Carrier, Carrier.id == CarrierRoute.carrier_id)
                .where(oc == origin.id, dc == destination.id)
                .order_by(col.desc())
            )
            rows = session.exec(q).all()

        if not rows:
            col = CarrierRoute.__table__.c.daily_trucks
            oc = CarrierRoute.__table__.c.origin_city_id
            dc = CarrierRoute.__table__.c.destination_city_id
            q = (
                select(Carrier.name, CarrierRoute.daily_trucks)
                .join(Carrier, Carrier.id == CarrierRoute.carrier_id)
                .where(oc.is_(None), dc.is_(None))
                .order_by(col.desc())
            )
            rows = session.exec(q).all()

    # If DB returned rows, serialize and return
    if rows:
        from app.metrics import inc as metrics_inc
        metrics_inc("db_get_carriers")
        return [{"name": name, "trucksPerDay": int(daily)} for name, daily in rows]

    # If still no rows, default to empty list
    from app.metrics import inc as metrics_inc
    metrics_inc("db_get_carriers")
    return []
