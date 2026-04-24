"""Search service: carrier lookup and deterministic route options.

This module contains the business logic for carrier ranking lookup and a small
set of deterministic mock routes used in functional tests.
"""

from __future__ import annotations

from typing import Dict, List

from app.providers import db as db_provider
from app.providers.maps import google, mock
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


def get_carriers_for_pair(from_place_id: str, to_place_id: str) -> List[Dict]:
    """Delegate carrier lookup to the DB provider.

    The provider encapsulates SQL access so services remain implementation
    independent and easier to test.
    """
    return db_provider.get_carriers_for_pair(from_place_id, to_place_id)


def get_routes_for_pair(from_place_id: str, to_place_id: str) -> List[Dict]:
    """Return route options using primary maps provider (Google) with DB-backed mock fallback.

    Try the Google provider first; if it raises or is unavailable, fall back to
    the local mock provider which derives deterministic routes from the DB.
    """
    primary = (settings.genlogs_maps_provider or "mock").lower()

    if primary == "google":
        try:
            return google.get_routes_for_pair(from_place_id, to_place_id)
        except Exception as exc:
            logger.warning("Primary maps provider (google) failed: %s; falling back to mock", exc)
            return mock.get_routes_for_pair(from_place_id, to_place_id)
    else:
        # If configured to use the mock provider as primary, just call it.
        return mock.get_routes_for_pair(from_place_id, to_place_id)
