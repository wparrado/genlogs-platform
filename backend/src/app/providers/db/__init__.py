"""Database provider wrapper.

This module exposes the database engine, session helpers and model classes
under the provider namespace app.providers.db so the rest of the application
can depend on a provider rather than direct modules.
"""

from .db import (
    engine,
    get_session,
    init_db,
    suggest_cities,
    get_carriers_for_pair,
    get_city_by_place_id,
)
from . import models
from .models import CityReference, Carrier, CarrierRoute

__all__ = [
    "engine",
    "get_session",
    "init_db",
    "suggest_cities",
    "get_carriers_for_pair",
    "models",
    "CityReference",
    "Carrier",
    "CarrierRoute",
]
