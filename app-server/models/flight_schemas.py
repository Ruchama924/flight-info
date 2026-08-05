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


class CodeshareInfo(BaseModel):
    airline_name: str | None = None
    flight_iata: str | None = None
    airline_iata: str | None = None


class FlightDetails(BaseModel):
    """Richer read-model for GET /flights/{flight_id} (Slice 3)."""

    flight_id: str
    airline: str
    origin: str
    destination: str
    departure_time: str | None = None
    arrival_time: str | None = None
    price: float
    stops: int = 0

    departure_airport: str | None = None
    departure_terminal: str | None = None
    departure_gate: str | None = None
    departure_delay_minutes: int | None = None

    arrival_airport: str | None = None
    arrival_terminal: str | None = None
    arrival_gate: str | None = None
    arrival_delay_minutes: int | None = None

    aircraft_registration: str | None = None
    aircraft_iata: str | None = None
    aircraft_icao: str | None = None

    flight_status: str | None = None
    codeshare: CodeshareInfo | None = None


class FlightSearchResponse(BaseModel):
    origin: str
    destination: str
    date: str
    count: int
    flights: list[FlightSummary]
    cache_hit: bool = False
