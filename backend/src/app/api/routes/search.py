"""API routes for search functionality."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.providers import db as db_provider
from app.providers.db.db import DatabaseUnavailable
from app.providers.logging_provider import get_logger
from app.services.search_service import (
    get_carriers_for_pair,
    get_routes_for_pair,
)

logger = get_logger(__name__)

router = APIRouter()


@router.get("/search")
async def search(
    from_id: Optional[str] = Query(None, alias="from_id"),
    to_id: Optional[str] = Query(None, alias="to_id"),
) -> JSONResponse:
    """Lookup carriers and routes for a city pair using query parameters.

    GET /api/search?from_id=...&to_id=...
    """
    # Basic presence validation
    if not from_id or not to_id:
        return JSONResponse(
            status_code=400,
            content={"code": "invalid_request", "message": "Both from_id and to_id are required"},
        )

    # Reject whitespace-only
    if not from_id.strip() or not to_id.strip():
        return JSONResponse(
            status_code=400,
            content={"code": "invalid_request", "message": "Whitespace-only city selection is not allowed"},
        )

    # Reject same id
    if from_id == to_id:
        return JSONResponse(
            status_code=400,
            content={"code": "invalid_request", "message": "Origin and destination must differ"},
        )

    # Basic format validation: accept any non-empty string; deeper checks happen later.
    def _valid_id_format(s: str) -> bool:
        return isinstance(s, str) and bool(s.strip())

    if not _valid_id_format(from_id) or not _valid_id_format(to_id):
        return JSONResponse(status_code=400, content={"code": "invalid_request", "message": "Malformed city id(s)"})

    # Resolve city metadata from DB when possible for richer response
    try:
        from_row = db_provider.get_city_by_place_id(from_id)
        to_row = db_provider.get_city_by_place_id(to_id)
    except DatabaseUnavailable as exc:
        logger.error("db.unavailable", extra={"error": str(exc)})
        return JSONResponse(status_code=503, content={"code": "service_unavailable", "message": "Database unavailable"})

    if not from_row or not to_row:
        return JSONResponse(
            status_code=400,
            content={"code": "invalid_request", "message": "Unknown city id(s)"},
        )

    try:
        carriers_list = get_carriers_for_pair(from_id, to_id)
        routes_list = get_routes_for_pair(from_id, to_id)
    except DatabaseUnavailable as exc:
        logger.error("db.unavailable", extra={"error": str(exc)})
        return JSONResponse(status_code=503, content={"code": "service_unavailable", "message": "Database unavailable"})

    response = {
        "from": {
            "id": from_row.place_id or str(from_row.id),
            "label": f"{from_row.name}, {from_row.state}, {from_row.country}",
            "city": from_row.name,
            "state": from_row.state,
            "country": from_row.country,
        },
        "to": {
            "id": to_row.place_id or str(to_row.id),
            "label": f"{to_row.name}, {to_row.state}, {to_row.country}",
            "city": to_row.name,
            "state": to_row.state,
            "country": to_row.country,
        },
        "routes": routes_list,
        "carriers": carriers_list,
    }

    return JSONResponse(status_code=200, content=response)
