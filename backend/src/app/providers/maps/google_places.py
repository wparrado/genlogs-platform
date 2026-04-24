"""Google Places (Autocomplete) provider.

Provides city suggestion functionality via the Google Places Autocomplete API.
This file complements the existing directions provider (google.py).
"""
from __future__ import annotations

from typing import Dict, List, Optional
import time
import requests
import logging

from app.config.settings import settings
from app.metrics import inc as metrics_inc
from app.providers import db as db_provider
import logging

logger = logging.getLogger(__name__)


def _call_google_places(input_text: str, api_key: str) -> Dict:
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {"input": input_text, "types": "(cities)", "key": api_key}
    r = requests.get(url, params=params, timeout=5)
    r.raise_for_status()
    return r.json()


def _call_find_place(text: str, api_key: str) -> Optional[Dict]:
    """Call Find Place from Text to enrich a DB city label with place_id.

    Returns a dict with place_id and optionally parsed components, or None on
    failure/not found.
    """
    try:
        url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        params = {"input": text, "inputtype": "textquery", "fields": "place_id,formatted_address,name,address_components", "key": api_key}
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        payload = r.json()
        cand = payload.get("candidates", [])
        if not cand:
            return None
        return cand[0]
    except Exception:
        return None


def get_place_details_by_id(place_id: str) -> Optional[Dict]:
    """Retrieve place details for a place_id using Place Details API.

    Returns a dict with keys name and address_components when available, or
    None on failure.
    """
    api_key = getattr(settings, "genlogs_google_api_key", None)
    if not api_key:
        return None
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {"place_id": place_id, "fields": "place_id,name,address_components,formatted_address", "key": api_key}
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        payload = r.json()
        result = payload.get("result")
        return result
    except Exception:
        return None


def get_city_suggestions(query: str, limit: int = 10) -> List[Dict]:
    """Return city suggestion items.

    Behavior:
    - Prefer suggestions from the DB (suggest_cities). For each DB result try to
      enrich with a Google place_id via Find Place (no DB writes).
    - If the DB has no matching suggestions, fall back to Google Places
      Autocomplete and return those results (no DB writes).

    Normalized shape mirrors database-backed suggestions: {id, label, city,
    state, country}
    """
    api_key = getattr(settings, "genlogs_google_api_key", None)
    if not api_key:
        logger.debug("Google Places API key not configured; raising to allow fallback")
        raise RuntimeError("Google Maps API key not configured")

    metrics_inc("maps_google_attempts")

    items: List[Dict] = []
    # First, try calling Google Autocomplete when an API key is available.
    try:
        payload = _call_google_places(query, api_key)
        preds = payload.get("predictions", [])[:limit]
        if preds:
            for p in preds:
                desc = p.get("description", "")
                parts = [s.strip() for s in desc.split(",")]
                city = parts[0] if parts else ""
                state = parts[1] if len(parts) > 1 else ""
                country = parts[-1] if parts else ""
                place_id = p.get("place_id") or desc
                items.append({
                    "id": place_id,
                    "label": desc,
                    "city": city,
                    "state": state,
                    "country": country,
                })
            return items
    except Exception:
        # If Google call fails, record failure and fall back to DB below
        metrics_inc("maps_google_failures")

    # If Google did not return results (or failed), fall back to DB-backed suggestions
    try:
        db_items = db_provider.suggest_cities(query, limit)
    except Exception:
        db_items = []

    for it in db_items:
        items.append({
            "id": it.get("id"),
            "label": it.get("label"),
            "city": it.get("city"),
            "state": it.get("state"),
            "country": it.get("country"),
        })

    return items[:limit]
