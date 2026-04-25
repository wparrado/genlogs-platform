"""Search service: carrier lookup and deterministic route options.

This module contains the business logic for carrier ranking lookup and a small
set of deterministic mock routes used in functional tests.
"""

from __future__ import annotations

from typing import Dict, List

from app.providers import db as db_provider
from app.providers.maps import google, mock
from app.config.settings import settings
from app.providers.logging_provider import get_logger
from app.telemetry import trace

logger = get_logger(__name__)


@trace()
def get_carriers_for_pair(from_place_id: str, to_place_id: str) -> List[Dict]:
    """Delegate carrier lookup to the DB provider.

    The provider encapsulates SQL access so services remain implementation
    independent and easier to test.
    """
    return db_provider.get_carriers_for_pair(from_place_id, to_place_id)


@trace()
def get_routes_for_pair(from_place_id: str, to_place_id: str) -> List[Dict]:
    """Return route options using primary maps provider (Google) with DB-backed mock fallback.

    Try the Google provider first; if it raises or is unavailable, fall back to
    the local mock provider which derives deterministic routes from the DB.
    """
    # In production flow: prefer primary (google) and only fall back to mock
    # if the primary provider raises or is unavailable. Tests can opt-in to
    # prefer the mock provider by setting the configuration flag.
    if getattr(settings, 'genlogs_prefer_mock_for_mock_ids', False) and from_place_id and to_place_id and from_place_id.startswith("mock:") and to_place_id.startswith("mock:"):
        routes = mock.get_routes_for_pair(from_place_id, to_place_id)
    else:
        routes = []
        api_key = getattr(settings, "genlogs_google_api_key", None)
        if api_key:
            try:
                routes = google.get_routes_for_pair(from_place_id, to_place_id)
            except Exception as exc:
                logger.warning("Primary maps provider (google) failed: %s; falling back to mock", exc)
                routes = mock.get_routes_for_pair(from_place_id, to_place_id)
        else:
            # No Google API key -> use mock provider
            routes = mock.get_routes_for_pair(from_place_id, to_place_id)

    # Ensure each route has a numeric duration (seconds) for sorting. Providers
    # may supply 'duration' (seconds) or only 'durationText'. Attempt to parse
    # durationText when necessary; otherwise treat missing durations as large.
    def _parse_duration_text(txt: str):
        if not txt:
            return None
        txt = txt.lower()
        h = 0
        m = 0
        try:
            if 'hr' in txt or 'hour' in txt:
                parts = txt.replace('hours', 'hr').replace('hour', 'hr').split('hr')
                h_part = parts[0].strip()
                h = int(h_part) if h_part.isdigit() else 0
                if len(parts) > 1 and 'min' in parts[1]:
                    m_part = parts[1].split('min')[0].strip()
                    m = int(m_part) if m_part.isdigit() else 0
            elif 'min' in txt:
                m = int(txt.split('min')[0].strip())
            return h * 3600 + m * 60
        except (ValueError, TypeError):
            return None

    for r in routes:
        if r.get('duration') is None:
            r['duration'] = _parse_duration_text(r.get('durationText')) or 10**9

    # Return top-3 fastest routes (smallest duration)
    routes_sorted = sorted(routes, key=lambda x: x.get('duration', 10**9))
    return routes_sorted[:3]
