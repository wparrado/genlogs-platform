"""Mock maps provider returning deterministic routes for canonical pairs.

This mirrors the small deterministic logic currently embedded in the
search_service; keeping it here makes it easy to switch services to the
provider later without changing behavior.
"""

from typing import Dict, List

from app.providers import db as db_provider


def _routes_for_labels(o_lbl: str, d_lbl: str) -> List[Dict]:
    """Map normalized labels to deterministic route payloads."""
    o_lbl = (o_lbl or "").lower()
    d_lbl = (d_lbl or "").lower()
    routes: List[Dict] = []

    def _parse_duration_text(txt: str) -> int:
        """Parse strings like '3 hr 52 min' into seconds. Return seconds or None on failure."""
        if not txt:
            return None
        txt = txt.lower()
        hours = 0
        mins = 0
        try:
            if 'hr' in txt or 'hour' in txt:
                # crude parse
                parts = txt.replace('hours', 'hr').replace('hour', 'hr').split('hr')
                hours = int(parts[0].strip()) if parts[0].strip().isdigit() else 0
                if len(parts) > 1 and 'min' in parts[1]:
                    mins_part = parts[1].split('min')[0].strip()
                    mins = int(mins_part) if mins_part.isdigit() else 0
            elif 'min' in txt:
                mins = int(txt.split('min')[0].strip())
            return hours * 3600 + mins * 60
        except Exception:
            return None

    if o_lbl == "new york, ny, us" and d_lbl == "washington, dc, us":
        routes = [
            {"id": "route_ny_was_1", "summary": "I-95 S", "durationText": "3 hr 52 min", "distanceText": "227 mi", "mapEmbedUrl": None, "pathPayload": None},
            {"id": "route_ny_was_2", "summary": "I-295 E", "durationText": "4 hr 10 min", "distanceText": "245 mi", "mapEmbedUrl": None, "pathPayload": None},
            {"id": "route_ny_was_3", "summary": "US-1 S", "durationText": "5 hr 05 min", "distanceText": "260 mi", "mapEmbedUrl": None, "pathPayload": None},
        ]
        # attach numeric duration for sorting
        for r in routes:
            r['duration'] = _parse_duration_text(r.get('durationText'))
    elif o_lbl == "san francisco, ca, us" and d_lbl == "los angeles, ca, us":
        routes = [
            {"id": "route_sf_la_1", "summary": "I-5 S", "durationText": "6 hr 30 min", "distanceText": "382 mi", "mapEmbedUrl": None, "pathPayload": None},
            {"id": "route_sf_la_2", "summary": "US-101 S", "durationText": "7 hr 15 min", "distanceText": "420 mi", "mapEmbedUrl": None, "pathPayload": None},
            {"id": "route_sf_la_3", "summary": "CA-1 S (scenic)", "durationText": "9 hr 00 min", "distanceText": "430 mi", "mapEmbedUrl": None, "pathPayload": None},
        ]

    return routes


def get_routes_for_pair(from_place_id: str, to_place_id: str) -> List[Dict]:
    """Return deterministic routes for canonical pairs using DB-backed cities.

    This provider queries the CityReference table for the given place_ids and
    maps normalized_label values to deterministic route payloads used by the
    UI and tests.
    """
    origin = db_provider.get_city_by_place_id(from_place_id)
    destination = db_provider.get_city_by_place_id(to_place_id)

    if not origin or not destination:
        # No DB match — return empty so callers can fallback to other providers
        return []

    return _routes_for_labels(origin.normalized_label, destination.normalized_label)