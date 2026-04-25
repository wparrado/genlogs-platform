"""Google Routes provider (ComputeRoutes).

This provider uses the Google Routes API (ComputeRoutes endpoint) via HTTP POST
... (docstring unchanged) ...
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional
import re

import requests

from app.config.settings import settings
from app.providers.logging_provider import get_logger
from app.telemetry import trace

logger = get_logger(__name__)

from app.metrics import inc as metrics_inc


class CircuitOpen(Exception):
    pass


class SimpleCircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_seconds: int = 60) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.failures = 0
        self.opened_at: Optional[float] = None

    def call(self, fn, *args, **kwargs):
        if self.opened_at:
            if time.time() - self.opened_at < self.recovery_seconds:
                raise CircuitOpen("circuit open")
            # recovery period elapsed — reset
            self.opened_at = None
            self.failures = 0

        try:
            res = fn(*args, **kwargs)
            # success: reset failure count
            self.failures = 0
            return res
        except Exception:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.opened_at = time.time()
            raise


_circuit = SimpleCircuitBreaker()


def _call_google_directions(origin: str, destination: str, api_key: str) -> Dict:
    """Use the Routes ComputeRoutes endpoint (POST) to request routes.

    Accepts place-like identifiers. For place IDs the Routes API expects a
    JSON body with origin.placeId and destination.placeId. computeAlternativeRoutes
    is set to true as requested. Field mask excludes polyline to avoid encoded
    polylines in the response.
    """
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"

    def _make_waypoint(p: Optional[str]):
        if not p:
            return None
        # strip leading 'place_id:' if present
        if isinstance(p, str) and p.startswith("place_id:"):
            return {"placeId": p.split("place_id:", 1)[1]}
        # common Place IDs begin with 'ChI'
        if isinstance(p, str) and p.startswith("ChI"):
            return {"placeId": p}
        # fallback: treat as address string
        return {"address": p}

    origin_wp = _make_waypoint(origin)
    destination_wp = _make_waypoint(destination)

    payload = {
        "origin": origin_wp,
        "destination": destination_wp,
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
        "computeAlternativeRoutes": True,
    }

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        # Request duration, distance, description and encoded polyline
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.description,routes.polyline.encodedPolyline",
    }

    r = requests.post(url, json=payload, headers=headers, timeout=5)
    r.raise_for_status()
    return r.json()


def _decode_polyline(polyline_str: str):
    """Decode an encoded polyline string into a list of [lat, lng] pairs.

    Implementation based on the Google polyline algorithm.
    """
    if not polyline_str:
        return []
    coords = []
    index = 0
    lat = 0
    lng = 0
    length = len(polyline_str)

    while index < length:
        shift = 0
        result = 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        shift = 0
        result = 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        coords.append([lat / 1e5, lng / 1e5])

    return coords


def _normalize_place_param(p: Optional[str]) -> Optional[str]:
    """Normalize a place identifier to the 'place_id:...' form when appropriate."""
    if not p:
        return p
    if isinstance(p, str) and p.startswith("place_id:"):
        return p
    if isinstance(p, str) and p.startswith("ChI"):
        return f"place_id:{p}"
    return p


def _extract_route_info(route: Dict, idx: int) -> Dict:
    """Convert a raw Google route object into the simplified internal schema.

    Extracts duration, distance, localized text and decodes encoded polylines.
    """
    summary = route.get("summary") or ""
    duration = None
    distance = None
    duration_text = ""
    distance_text = ""

    # Prefer route-level duration and distance (ComputeRoutes shape)
    route_duration = route.get("duration")
    if route_duration is not None:
        if isinstance(route_duration, str) and route_duration.endswith("s"):
            try:
                duration = int(float(route_duration[:-1]))
                duration_text = route_duration
            except Exception:
                duration = None
                duration_text = str(route_duration)
        elif isinstance(route_duration, dict):
            duration = route_duration.get("value") or route_duration.get("seconds")
            duration_text = route_duration.get("text", "")

    distance = route.get("distanceMeters") or None

    # Fallback to legs localized text if present
    legs = route.get("legs", [])
    if legs and isinstance(legs, list) and len(legs) > 0:
        l0 = legs[0]
        if isinstance(l0.get("duration"), dict):
            duration_text = l0.get("duration").get("text", duration_text)
        if isinstance(l0.get("distance"), dict):
            distance_text = l0.get("distance").get("text", distance_text)

    # Try to extract encoded polyline from route.polyline.encodedPolyline
    path_payload = None
    poly = route.get("polyline") or {}
    if isinstance(poly, dict):
        encoded = poly.get("encodedPolyline") or poly.get("encoded_polyline") or None
        if encoded:
            path_payload = _decode_polyline(encoded)

    route_desc = route.get("description") or f"google_{idx}"
    sanitized_route_id = re.sub(r'[^A-Za-z0-9_\-]', '', route_desc.replace(' ', '-'))

    return {
        "id": sanitized_route_id,
        "summary": summary,
        "duration": duration,
        "distance": distance,
        "durationText": duration_text,
        "distanceText": distance_text,
        "mapEmbedUrl": None,
        "pathPayload": path_payload,
    }


@trace()
def get_routes_for_pair(from_place_id: str, to_place_id: str) -> List[Dict]:
    """Attempt to fetch route options from Google Directions API.

    For MVP the provider accepts plaintext place identifiers. If no API key is
    configured a RuntimeError is raised so callers can fallback to an alternate
    provider.
    """
    api_key = getattr(settings, "genlogs_google_api_key", None)
    if not api_key:
        logger.debug("Google Maps API key not configured; raising to allow fallback")
        raise RuntimeError("Google Maps API key not configured")

    # Simple retry with exponential backoff
    backoff = 0.5
    last_exc: Optional[Exception] = None
    for attempt in range(3):
        try:
            metrics_inc("maps_google_attempts")
            origin_param = _normalize_place_param(from_place_id)
            destination_param = _normalize_place_param(to_place_id)
            payload = _circuit.call(_call_google_directions, origin_param, destination_param, api_key)

            routes = [_extract_route_info(route, idx) for idx, route in enumerate(payload.get("routes", [])[:3])]

            # Sort routes by duration ascending (shortest first). Routes with unknown duration are placed last.
            routes.sort(key=lambda r: (r.get("duration") is None, r.get("duration") or 0))
            return routes
        except CircuitOpen:
            metrics_inc("maps_google_circuit_open")
            raise
        except Exception as exc:
            metrics_inc("maps_google_failures")
            last_exc = exc
            time.sleep(backoff)
            backoff *= 2

    # If all retries fail, raise the last exception
    if last_exc:
        raise last_exc
    return []
