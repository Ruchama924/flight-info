from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from events.user_events import UserRegistered
from repositories.event_store import EventStoreRepository

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "flight-advisor-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


@dataclass(frozen=True)
class LoginQuery:
    email: str
    password: str


@dataclass(frozen=True)
class LoginResult:
    access_token: str
    user_id: str
    email: str


class InvalidCredentialsError(Exception):
    pass


class LoginUserHandler:
    def __init__(self, event_store: EventStoreRepository) -> None:
        self._event_store = event_store

    def handle(self, query: LoginQuery) -> LoginResult:
        user = self._project_user_by_email(query.email.strip().lower())
        if user is None or not _pwd_context.verify(query.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")

        token = jwt.encode(
            {
                "sub": user.user_id,
                "email": user.email,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        return LoginResult(access_token=token, user_id=user.user_id, email=user.email)

    def _project_user_by_email(self, email: str) -> UserRegistered | None:
        for stored in self._event_store.get_events_by_type("UserRegistered"):
            if stored.payload.get("email", "").lower() == email:
                return UserRegistered.from_payload(stored.payload)
        return None
