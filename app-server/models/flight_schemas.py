from __future__ import annotations

from pydantic import BaseModel, Field


class FlightSummary(BaseModel):
    flight_id: str
    airline: str
    origin: str
    destination: str
    departure_time: str | None = None
    arrival_time: str | None = None
    price: float = Field(description="USD; may be a free-tier mock placeholder")
    stops: int = 0


class FlightSearchResponse(BaseModel):
    origin: str
    destination: str
    date: str
    count: int
    flights: list[FlightSummary]
    cache_hit: bool = False
