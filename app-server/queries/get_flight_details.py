from __future__ import annotations

import logging
from dataclasses import dataclass

from models.flight_schemas import FlightDetails
from queries.search_flights import SearchFlightsHandler

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GetFlightDetailsQuery:
    flight_id: str


class FlightNotFoundError(Exception):
    pass


class GetFlightDetailsHandler:
    """Resolve flight details from recent search cache (no extra AviationStack call)."""

    def __init__(self, search_handler: SearchFlightsHandler) -> None:
        self._search_handler = search_handler

    def handle(self, query: GetFlightDetailsQuery) -> FlightDetails:
        flight_id = query.flight_id.strip()
        logger.info("GetFlightDetails flight_id=%s", flight_id)
        details = self._search_handler.find_cached_details(flight_id)
        if details is None:
            raise FlightNotFoundError(
                f"Flight '{flight_id}' was not found in any recent search cache. "
                "Run a search first, then open details within ~10 minutes."
            )
        return details
