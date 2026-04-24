"""City suggestion endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services.city_service import suggest_cities

router = APIRouter()


@router.get("/cities")
async def city_suggestions(query: Optional[str] = Query(None)) -> JSONResponse:
    """Return normalized city suggestions or validation errors.

    Query must be at least length 2 after trimming. Returns:
    {"items": [ {id, label, city, state, country}, ... ]}
    """
    if query is None:
        return JSONResponse(
            status_code=400,
            content={"code": "invalid_query", "message": "query parameter is required"},
        )

    q = query.strip()
    if len(q) < 2:
        return JSONResponse(
            status_code=400,
            content={"code": "invalid_query", "message": "query must be at least 2 characters"},
        )

    items: List[dict] = suggest_cities(q)

    return JSONResponse(status_code=200, content={"items": items})
