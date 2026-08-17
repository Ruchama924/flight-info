from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from events.booking_events import BookingCreated
from queries.get_flight_details import GetFlightDetailsHandler, GetFlightDetailsQuery
from repositories.event_store import EventStoreRepository


@dataclass(frozen=True)
class CreateBookingCommand:
    user_id: str
    flight_id: str
    passenger_name: str
    passport_number: str


class CreateBookingHandler:
    def __init__(
        self,
        event_store: EventStoreRepository,
        details_handler: GetFlightDetailsHandler,
    ) -> None:
        self._event_store = event_store
        self._details_handler = details_handler

    def handle(self, command: CreateBookingCommand) -> BookingCreated:
        flight_id = command.flight_id.strip()
        passenger_name = command.passenger_name.strip()
        passport_number = command.passport_number.strip()

        # Validate flight exists in recent search cache (same path as Slice 3 details).
        self._details_handler.handle(GetFlightDetailsQuery(flight_id=flight_id))

        booking_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)

        event = BookingCreated(
            booking_id=booking_id,
            user_id=command.user_id,
            flight_id=flight_id,
            passenger_name=passenger_name,
            passport_number=passport_number,
            created_at=created_at,
        )
        self._event_store.append_event(event.event_type, event.to_payload(), created_at)
        return event
