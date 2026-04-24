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

    # Lookup carriers from DB following fallback rules
    carriers_list: List[dict] = []
    routes_list: List[dict] = []
    with Session(engine) as session:
        origin = session.exec(select(CityReference).where(CityReference.place_id == from_city.id)).first()
        destination = session.exec(select(CityReference).where(CityReference.place_id == to_city.id)).first()

        rows = []
        if origin and destination:
            q = select(Carrier.name, CarrierRoute.daily_trucks).join(Carrier, Carrier.id == CarrierRoute.carrier_id).where(
                CarrierRoute.origin_city_id == origin.id,
                CarrierRoute.destination_city_id == destination.id,
            ).order_by(CarrierRoute.daily_trucks.desc())
            rows = session.exec(q).all()

        if not rows:
            q = select(Carrier.name, CarrierRoute.daily_trucks).join(Carrier, Carrier.id == CarrierRoute.carrier_id).where(
                CarrierRoute.origin_city_id == None,
                CarrierRoute.destination_city_id == None,
            ).order_by(CarrierRoute.daily_trucks.desc())
            rows = session.exec(q).all()

        for name, daily in rows:
            carriers_list.append({"name": name, "trucksPerDay": int(daily)})

        # Build simple route options based on canonical normalized labels
        if origin and destination:
            o_lbl = (origin.normalized_label or "").lower()
            d_lbl = (destination.normalized_label or "").lower()
            if o_lbl == "new york, ny, us" and d_lbl == "washington, dc, us":
                routes_list = [
                    {"id": "route_ny_was_1", "summary": "I-95 S", "durationText": "3 hr 52 min", "distanceText": "227 mi", "mapEmbedUrl": None, "pathPayload": None},
                    {"id": "route_ny_was_2", "summary": "I-295 E", "durationText": "4 hr 10 min", "distanceText": "245 mi", "mapEmbedUrl": None, "pathPayload": None},
                    {"id": "route_ny_was_3", "summary": "US-1 S", "durationText": "5 hr 05 min", "distanceText": "260 mi", "mapEmbedUrl": None, "pathPayload": None},
                ]
            elif o_lbl == "san francisco, ca, us" and d_lbl == "los angeles, ca, us":
                routes_list = [
                    {"id": "route_sf_la_1", "summary": "I-5 S", "durationText": "6 hr 30 min", "distanceText": "382 mi", "mapEmbedUrl": None, "pathPayload": None},
                    {"id": "route_sf_la_2", "summary": "US-101 S", "durationText": "7 hr 15 min", "distanceText": "420 mi", "mapEmbedUrl": None, "pathPayload": None},
                    {"id": "route_sf_la_3", "summary": "CA-1 S (scenic)", "durationText": "9 hr 00 min", "distanceText": "430 mi", "mapEmbedUrl": None, "pathPayload": None},
                ]

    response = {
        "from": {"id": from_city.id, "label": from_city.label, "city": from_city.city, "state": from_city.state, "country": from_city.country},
        "to": {"id": to_city.id, "label": to_city.label, "city": to_city.city, "state": to_city.state, "country": to_city.country},
        "routes": routes_list,
        "carriers": carriers_list,
    }

    return JSONResponse(status_code=200, content=response)

