"""Search and carrier lookup endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError, ConfigDict
from typing import List
from sqlmodel import Session, select
from app.db import engine
from app.models.db_models import CityReference, CarrierRoute, Carrier

router = APIRouter()


class SearchCityModel(BaseModel):
    id: str
    label: str
    city: str
    state: str
    country: str


class SearchRequestModel(BaseModel):
    model_config = ConfigDict(validate_by_name=True)
    from_: SearchCityModel = Field(..., alias="from")
    to: SearchCityModel


@router.post("/search")
async def search(request: Request) -> JSONResponse:
    """Validate request payload and return carriers for the route.

    Validation errors and business-rule violations map to 400 with a stable
    error shape. Successful responses follow the SearchResponse contract.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"code": "invalid_request", "message": "Invalid JSON payload"})

    try:
        req = SearchRequestModel.model_validate(payload)
    except ValidationError as exc:
        return JSONResponse(status_code=400, content={"code": "invalid_request", "message": "Malformed payload", "details": str(exc)})

    from_city = req.from_
    to_city = req.to

    # Reject whitespace-only fields
    if not from_city.id.strip() or not from_city.label.strip() or not to_city.id.strip() or not to_city.label.strip():
        return JSONResponse(status_code=400, content={"code": "invalid_request", "message": "Whitespace-only city selection is not allowed"})

    # Reject same canonical city (based on id)
    if from_city.id == to_city.id:
        return JSONResponse(status_code=400, content={"code": "invalid_request", "message": "Origin and destination must differ"})

    # Delegate carrier lookup and route generation to service layer
    from app.services.search_service import get_carriers_for_pair, get_routes_for_pair

    carriers_list = get_carriers_for_pair(from_city.id, to_city.id)
    routes_list = get_routes_for_pair(from_city.id, to_city.id)

    response = {
        "from": {"id": from_city.id, "label": from_city.label, "city": from_city.city, "state": from_city.state, "country": from_city.country},
        "to": {"id": to_city.id, "label": to_city.label, "city": to_city.city, "state": to_city.state, "country": to_city.country},
        "routes": routes_list,
        "carriers": carriers_list,
    }

    return JSONResponse(status_code=200, content=response)

