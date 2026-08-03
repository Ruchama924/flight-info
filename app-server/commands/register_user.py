from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from passlib.context import CryptContext

from events.user_events import UserRegistered
from repositories.event_store import EventStoreRepository

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass(frozen=True)
class RegisterUserCommand:
    email: str
    password: str


class EmailAlreadyRegisteredError(Exception):
    pass


class RegisterUserHandler:
    def __init__(self, event_store: EventStoreRepository) -> None:
        self._event_store = event_store

    def handle(self, command: RegisterUserCommand) -> UserRegistered:
        normalized_email = command.email.strip().lower()

        for stored in self._event_store.get_events_by_type("UserRegistered"):
            if stored.payload.get("email", "").lower() == normalized_email:
                raise EmailAlreadyRegisteredError(f"Email already registered: {normalized_email}")

        user_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        password_hash = _pwd_context.hash(command.password)

        event = UserRegistered(
            user_id=user_id,
            email=normalized_email,
            password_hash=password_hash,
            created_at=created_at,
        )
        self._event_store.append_event(event.event_type, event.to_payload(), created_at)
        return event
