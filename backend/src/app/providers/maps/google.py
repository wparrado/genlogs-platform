"""Google Maps provider (minimal, no extra deps).

This provider attempts to call the Google Directions API when a key is
configured via settings.google_maps_api_key. To keep the runtime free of new
dependencies the implementation uses requests only. The provider implements a
small, local circuit-breaker and a simple retry/backoff loop.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

import requests

from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

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
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {"origin": origin, "destination": destination, "mode": "driving", "key": api_key}
    r = requests.get(url, params=params, timeout=5)
    r.raise_for_status()
    return r.json()


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
            payload = _circuit.call(_call_google_directions, from_place_id, to_place_id, api_key)
            routes = []
            for idx, leg in enumerate(payload.get("routes", [])[:3]):
                # Derive a compact representation similar to mocks
                summary = leg.get("summary") or ""
                legs = leg.get("legs", [])
                duration_text = ""
                distance_text = ""
                if legs:
                    duration = legs[0].get("duration", {}).get("value")
                    distance = legs[0].get("distance", {}).get("value")
                    duration_text = legs[0].get("duration", {}).get("text", "")
                    distance_text = legs[0].get("distance", {}).get("text", "")
                else:
                    duration = None
                    distance = None
                    duration_text = ""
                    distance_text = ""
                routes.append(
                    {
                        "id": f"google_{idx}",
                        "summary": summary,
                        "duration": duration,
                        "distance": distance,
                        "durationText": duration_text,
                        "distanceText": distance_text,
                        "mapEmbedUrl": None,
                        "pathPayload": None,
                    }
                )
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
