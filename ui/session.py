from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UserSession:
    access_token: str
    user_id: str
    email: str


class SessionStore:
    """In-memory session holder for Slice 1 (no persistence yet)."""

    def __init__(self) -> None:
        self._session: UserSession | None = None

    @property
    def session(self) -> UserSession | None:
        return self._session

    def set_session(self, access_token: str, user_id: str, email: str) -> None:
        self._session = UserSession(
            access_token=access_token,
            user_id=user_id,
            email=email,
        )

    def clear(self) -> None:
        self._session = None
