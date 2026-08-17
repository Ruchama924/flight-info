from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from events.booking_events import BookingCreated
from models.booking_schemas import BookingSummary
from queries.search_flights import SearchFlightsHandler
from repositories.event_store import EventStoreRepository


@dataclass(frozen=True)
class GetMyBookingsQuery:
    user_id: str


class GetMyBookingsHandler:
    def __init__(
        self,
        event_store: EventStoreRepository,
        search_handler: SearchFlightsHandler,
    ) -> None:
        self._event_store = event_store
        self._search_handler = search_handler

    def handle(self, query: GetMyBookingsQuery) -> list[BookingSummary]:
        user_id = query.user_id

        # --- Event replay projection ---
        # Step 1: collect this user's BookingCreated events from the event stream.
        created_bookings: list[BookingCreated] = []
        for stored in self._event_store.get_events_by_user(user_id):
            if stored.event_type != "BookingCreated":
                continue
            created_bookings.append(BookingCreated.from_payload(stored.payload))

        # Step 2: collect all BookingCancelled booking_ids (global stream).
        # BookingCancelled has no user_id in its payload, so we scan by type.
        cancelled_ids: set[str] = set()
        for stored in self._event_store.get_events_by_type("BookingCancelled"):
            booking_id = stored.payload.get("booking_id")
            if booking_id:
                cancelled_ids.add(str(booking_id))

        # Step 3: project current read-model state — bookings are never deleted,
        # only marked cancelled when a matching BookingCancelled event exists.
        summaries: list[BookingSummary] = []
        for created in created_bookings:
            status: Literal["active", "cancelled"] = (
                "cancelled" if created.booking_id in cancelled_ids else "active"
            )
            flight = self._search_handler.find_cached_details(created.flight_id)
            summaries.append(
                BookingSummary(
                    booking_id=created.booking_id,
                    flight_id=created.flight_id,
                    passenger_name=created.passenger_name,
                    passport_number=created.passport_number,
                    status=status,
                    created_at=created.created_at,
                    airline=flight.airline if flight else None,
                    origin=flight.origin if flight else None,
                    destination=flight.destination if flight else None,
                    departure_time=flight.departure_time if flight else None,
                )
            )

        summaries.sort(key=lambda item: item.created_at, reverse=True)
        return summaries
