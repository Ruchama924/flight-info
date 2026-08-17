from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from events.booking_events import BookingCancelled, BookingCreated
from repositories.event_store import EventStoreRepository


@dataclass(frozen=True)
class CancelBookingCommand:
    user_id: str
    booking_id: str


class BookingNotFoundError(Exception):
    pass


class BookingForbiddenError(Exception):
    pass


class BookingAlreadyCancelledError(Exception):
    pass


class CancelBookingHandler:
    def __init__(self, event_store: EventStoreRepository) -> None:
        self._event_store = event_store

    def handle(self, command: CancelBookingCommand) -> BookingCancelled:
        booking_id = command.booking_id.strip()

        created: BookingCreated | None = None
        for stored in self._event_store.get_events_by_type("BookingCreated"):
            if stored.payload.get("booking_id") == booking_id:
                created = BookingCreated.from_payload(stored.payload)
                break

        if created is None:
            raise BookingNotFoundError(f"Booking not found: {booking_id}")

        if created.user_id != command.user_id:
            raise BookingForbiddenError("You do not have permission to cancel this booking.")

        for stored in self._event_store.get_events_by_type("BookingCancelled"):
            if stored.payload.get("booking_id") == booking_id:
                raise BookingAlreadyCancelledError(f"Booking already cancelled: {booking_id}")

        cancelled_at = datetime.now(timezone.utc)
        event = BookingCancelled(booking_id=booking_id, cancelled_at=cancelled_at)
        self._event_store.append_event(event.event_type, event.to_payload(), cancelled_at)
        return event
