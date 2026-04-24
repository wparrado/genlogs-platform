from __future__ import annotations
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
import uuid
from sqlalchemy import Column, String, SmallInteger, Boolean, CheckConstraint, UniqueConstraint, ForeignKey


class CityReference(SQLModel, table=True):
    __tablename__ = "city_reference"

    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    place_id: Optional[str] = Field(default=None, sa_column=Column(String(255), unique=True, index=True))
    name: str = Field(sa_column=Column(String(100), nullable=False))
    state: str = Field(sa_column=Column(String(100), nullable=False))
    country: str = Field(default="US", sa_column=Column(String(10), nullable=False))
    normalized_label: str = Field(sa_column=Column(String(200), nullable=False, index=True))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)




class Carrier(SQLModel, table=True):
    __tablename__ = "carriers"

    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(sa_column=Column(String(200), nullable=False, unique=True))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)




class CarrierRoute(SQLModel, table=True):
    __tablename__ = "carrier_routes"
    __table_args__ = (
        UniqueConstraint("origin_city_id", "destination_city_id", "carrier_id", name="uix_route_carrier"),
        CheckConstraint("(origin_city_id IS NULL) = (destination_city_id IS NULL)", name="ck_both_null_or_both_not_null"),
    )

    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    origin_city_id: Optional[uuid.UUID] = Field(default=None, sa_column=Column(ForeignKey("city_reference.id"), nullable=True))
    destination_city_id: Optional[uuid.UUID] = Field(default=None, sa_column=Column(ForeignKey("city_reference.id"), nullable=True))
    carrier_id: uuid.UUID = Field(sa_column=Column(ForeignKey("carriers.id"), nullable=False))
    daily_trucks: int = Field(sa_column=Column(SmallInteger, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


