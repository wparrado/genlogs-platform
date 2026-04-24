"""City suggestion service used by the API.

Provides a small wrapper around DB queries that returns JSON-serializable
structures suitable for the /api/cities endpoint.
"""

from __future__ import annotations

from typing import Dict, List

from app.providers import db as db_provider


def suggest_cities(prefix: str, limit: int = 10) -> List[Dict]:
    """Return up to ``limit`` cities whose normalized_label starts with prefix.

    Delegates DB access to the provider layer.
    """
    return db_provider.suggest_cities(prefix, limit)
