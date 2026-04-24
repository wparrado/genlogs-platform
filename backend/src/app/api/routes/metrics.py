"""Metrics endpoint exposing Prometheus metrics when available, JSON fallback otherwise."""
from fastapi import APIRouter, Response

from app.metrics import prometheus_metrics_latest, prometheus_content_type, get

router = APIRouter()


@router.get("/metrics")
async def metrics():
    data = prometheus_metrics_latest()
    if data is not None:
        return Response(content=data, media_type=prometheus_content_type())

    # Fallback JSON mapping for local/dev when prometheus_client is not installed
    keys = [
        "maps_google_attempts",
        "maps_google_failures",
        "maps_google_circuit_open",
        "db_get_carriers",
    ]
    return {k: get(k) for k in keys}
