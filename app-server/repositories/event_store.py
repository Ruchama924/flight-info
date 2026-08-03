from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StoredEvent:
    id: int
    event_type: str
    payload: dict[str, Any]
    timestamp: datetime


class EventStoreRepository(ABC):
    @abstractmethod
    def append_event(self, event_type: str, payload: dict[str, Any], timestamp: datetime) -> None:
        """Persist a domain event."""

    @abstractmethod
    def get_events_by_user(self, user_id: str) -> list[StoredEvent]:
        """Return all events whose payload contains the given user_id."""

    @abstractmethod
    def get_events_by_type(self, event_type: str) -> list[StoredEvent]:
        """Return all events of a given type (used for projections and uniqueness checks)."""


class SQLiteEventStore(EventStoreRepository):
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def append_event(self, event_type: str, payload: dict[str, Any], timestamp: datetime) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events (event_type, payload, timestamp)
                VALUES (?, ?, ?)
                """,
                (event_type, json.dumps(payload), timestamp.isoformat()),
            )
            conn.commit()

    def get_events_by_user(self, user_id: str) -> list[StoredEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, event_type, payload, timestamp FROM events ORDER BY id ASC"
            ).fetchall()
        return [stored for row in rows if (stored := self._row_to_event(row)).payload.get("user_id") == user_id]

    def get_events_by_type(self, event_type: str) -> list[StoredEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, event_type, payload, timestamp
                FROM events
                WHERE event_type = ?
                ORDER BY id ASC
                """,
                (event_type,),
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> StoredEvent:
        return StoredEvent(
            id=row["id"],
            event_type=row["event_type"],
            payload=json.loads(row["payload"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )
