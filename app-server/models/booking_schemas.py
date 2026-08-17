from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CreateBookingRequest(BaseModel):
    flight_id: str = Field(min_length=1)
    passenger_name: str = Field(min_length=1)
    passport_number: str = Field(min_length=1)


class CreateBookingResponse(BaseModel):
    booking_id: str
    flight_id: str
    passenger_name: str
    status: Literal["active"] = "active"
    created_at: datetime


class BookingSummary(BaseModel):
    booking_id: str
    flight_id: str
    passenger_name: str
    passport_number: str
    status: Literal["active", "cancelled"]
    created_at: datetime
    airline: str | None = None
    origin: str | None = None
    destination: str | None = None
    departure_time: str | None = None


class MyBookingsResponse(BaseModel):
    count: int
    bookings: list[BookingSummary]


class CancelBookingResponse(BaseModel):
    booking_id: str
    status: Literal["cancelled"] = "cancelled"
    cancelled_at: datetime
