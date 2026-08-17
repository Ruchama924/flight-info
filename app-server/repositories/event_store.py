from __future__ import annotations

import json
import logging
import sqlite3
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pyodbc

logger = logging.getLogger(__name__)

ODBC_DRIVER = "{ODBC Driver 18 for SQL Server}"
EVENTS_TABLE = "events"


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


def _build_somee_connection_string(server: str, database: str, uid: str, pwd: str) -> str:
    """Build a pyodbc connection string (not the raw ADO.NET string from somee dashboard)."""
    return (
        f"DRIVER={ODBC_DRIVER};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={uid};"
        f"PWD={pwd};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )


class SomeeEventStore(EventStoreRepository):
    def __init__(self, server: str, database: str, uid: str, pwd: str) -> None:
        self._conn_str = _build_somee_connection_string(server, database, uid, pwd)
        self._lock = threading.Lock()
        self._conn: pyodbc.Connection | None = None
        self._schema_ready = False

    def _connect(self) -> pyodbc.Connection:
        if self._conn is not None:
            try:
                self._conn.cursor().execute("SELECT 1")
                return self._conn
            except pyodbc.Error:
                logger.warning("somee event store connection lost; reconnecting")
                try:
                    self._conn.close()
                except pyodbc.Error:
                    pass
                self._conn = None
                self._schema_ready = False

        conn = pyodbc.connect(self._conn_str, timeout=30)
        conn.autocommit = False
        self._conn = conn
        if not self._schema_ready:
            self._init_schema(conn)
            self._schema_ready = True
        return conn

    def _init_schema(self, conn: pyodbc.Connection) -> None:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            IF NOT EXISTS (
                SELECT 1 FROM sys.tables WHERE name = '{EVENTS_TABLE}'
            )
            BEGIN
                CREATE TABLE {EVENTS_TABLE} (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    event_type NVARCHAR(255) NOT NULL,
                    payload NVARCHAR(MAX) NOT NULL,
                    timestamp NVARCHAR(64) NOT NULL
                );
            END
            """
        )
        conn.commit()

    def append_event(self, event_type: str, payload: dict[str, Any], timestamp: datetime) -> None:
        with self._lock:
            conn = self._connect()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    f"""
                    INSERT INTO {EVENTS_TABLE} (event_type, payload, timestamp)
                    VALUES (?, ?, ?)
                    """,
                    (event_type, json.dumps(payload), timestamp.isoformat()),
                )
                conn.commit()
            except pyodbc.Error:
                conn.rollback()
                raise

    def get_events_by_user(self, user_id: str) -> list[StoredEvent]:
        with self._lock:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT id, event_type, payload, timestamp FROM {EVENTS_TABLE} ORDER BY id ASC"
            )
            rows = cursor.fetchall()
        return [
            stored
            for row in rows
            if (stored := self._row_to_event(row)).payload.get("user_id") == user_id
        ]

    def get_events_by_type(self, event_type: str) -> list[StoredEvent]:
        with self._lock:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT id, event_type, payload, timestamp
                FROM {EVENTS_TABLE}
                WHERE event_type = ?
                ORDER BY id ASC
                """,
                (event_type,),
            )
            rows = cursor.fetchall()
        return [self._row_to_event(row) for row in rows]

    @staticmethod
    def _row_to_event(row: pyodbc.Row) -> StoredEvent:
        return StoredEvent(
            id=row.id,
            event_type=row.event_type,
            payload=json.loads(row.payload),
            timestamp=datetime.fromisoformat(row.timestamp),
        )
