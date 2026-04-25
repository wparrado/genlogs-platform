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

    Always prefer Google Places when an API key is configured. If Google is not
    configured or the call fails, fall back to the DB provider. This keeps the
    behavior consistent in production while preserving CSV/test fallbacks.
    """
    api_key = getattr(settings, "genlogs_google_api_key", None)
    if api_key:
        try:
            return google_places.get_city_suggestions(prefix, limit)
        except Exception:
            # On any Google error, fall back to DB suggestions
            return db_provider.suggest_cities(prefix, limit)

    # If tests opt-in to prefer mock IDs via CSV, allow that behavior only if no API key is configured
    if getattr(settings, "genlogs_prefer_mock_for_mock_ids", False):
        # Delegate to DB provider's CSV-aware suggest_cities which already
        # checks the bundled placeid_mappings.csv when configured.
        return db_provider.suggest_cities(prefix, limit)

    # No API key configured — use DB provider
    return db_provider.suggest_cities(prefix, limit)
