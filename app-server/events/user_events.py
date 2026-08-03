from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class UserRegistered:
    user_id: str
    email: str
    password_hash: str
    created_at: datetime

    @property
    def event_type(self) -> str:
        return "UserRegistered"

    def to_payload(self) -> dict:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_payload(cls, payload: dict) -> "UserRegistered":
        created_at = payload["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        return cls(
            user_id=payload["user_id"],
            email=payload["email"],
            password_hash=payload["password_hash"],
            created_at=created_at,
        )
