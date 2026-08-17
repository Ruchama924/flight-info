from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class BookingCreated:
    booking_id: str
    user_id: str
    flight_id: str
    passenger_name: str
    passport_number: str
    created_at: datetime

    @property
    def event_type(self) -> str:
        return "BookingCreated"

    def to_payload(self) -> dict:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_payload(cls, payload: dict) -> "BookingCreated":
        created_at = payload["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        return cls(
            booking_id=payload["booking_id"],
            user_id=payload["user_id"],
            flight_id=payload["flight_id"],
            passenger_name=payload["passenger_name"],
            passport_number=payload["passport_number"],
            created_at=created_at,
        )


@dataclass(frozen=True)
class BookingCancelled:
    booking_id: str
    cancelled_at: datetime

    @property
    def event_type(self) -> str:
        return "BookingCancelled"

    def to_payload(self) -> dict:
        data = asdict(self)
        data["cancelled_at"] = self.cancelled_at.isoformat()
        return data

    @classmethod
    def from_payload(cls, payload: dict) -> "BookingCancelled":
        cancelled_at = payload["cancelled_at"]
        if isinstance(cancelled_at, str):
            cancelled_at = datetime.fromisoformat(cancelled_at)
        return cls(
            booking_id=payload["booking_id"],
            cancelled_at=cancelled_at,
        )
