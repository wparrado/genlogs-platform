"""City suggestion service used by the API.

Provides a small wrapper around DB queries that returns JSON-serializable
structures suitable for the /api/cities endpoint.
"""

from __future__ import annotations

from typing import Dict, List

from app.providers import db as db_provider
from app.providers.maps import google_places
from app.config.settings import settings


def suggest_cities(prefix: str, limit: int = 10) -> List[Dict]:
    """Return up to ``limit`` cities whose normalized_label starts with prefix.

    If the configured maps provider is 'google' the service will attempt to
    fetch suggestions from the Google Places API and fall back to the DB when
    unavailable. Otherwise, it delegates to the DB provider.
    """
    primary = (settings.genlogs_maps_provider or "mock").lower()
    if primary == "google":
        try:
            return google_places.get_city_suggestions(prefix, limit)
        except Exception:
            return db_provider.suggest_cities(prefix, limit)

    return db_provider.suggest_cities(prefix, limit)
