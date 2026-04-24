from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from typing import List, Optional
from app.db import engine
from app.models.db_models import CityReference

router = APIRouter()


@router.get("/cities")
async def city_suggestions(query: Optional[str] = Query(None)) -> JSONResponse:
    """Return normalized city suggestions or validation errors.

    Query must be at least length 2 after trimming. Returns:
    {"items": [ {id, label, city, state, country}, ... ]}
    """
    if query is None:
        return JSONResponse(status_code=400, content={"code": "invalid_query", "message": "query parameter is required"})

    q = query.strip()
    if len(q) < 2:
        return JSONResponse(status_code=400, content={"code": "invalid_query", "message": "query must be at least 2 characters"})

    prefix = q.lower()
    items: List[dict] = []
    with Session(engine) as session:
        stmt = select(CityReference).where(CityReference.normalized_label.like(prefix + "%")).order_by(CityReference.normalized_label).limit(10)
        rows = session.exec(stmt).all()
        for r in rows:
            items.append({
                "id": r.place_id or str(r.id),
                "label": f"{r.name}, {r.state}, {r.country}",
                "city": r.name,
                "state": r.state,
                "country": r.country,
            })

    return JSONResponse(status_code=200, content={"items": items})
