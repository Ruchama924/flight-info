"""Isolated spike: prove Python on this machine can read/write somee.com MS SQL.

Run:  .\\.venv\\Scripts\\python.exe test_connection.py
(from scratch/somee_spike, after copying .env.example to .env)
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

TABLE_NAME = "spike_events_test"
TEST_NOTE = "FlightAdvisor somee.com spike — safe to delete"
ODBC_DRIVER = "{ODBC Driver 18 for SQL Server}"


def _load_raw_env_value() -> str:
    """Read SOMEE_CONNECTION_STRING from scratch/somee_spike/.env"""
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)
    raw = os.getenv("SOMEE_CONNECTION_STRING", "").strip()
    if not raw:
        print(
            "FAIL: SOMEE_CONNECTION_STRING is missing.\n"
            f"Copy .env.example to .env in {env_path.parent} and paste your "
            "somee.com connection string.",
            file=sys.stderr,
        )
        sys.exit(1)
    return raw.strip('"').strip("'")


def _parse_key_value_pairs(raw: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for part in raw.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, _, value = part.partition("=")
        pairs[key.strip().lower()] = value.strip()
    return pairs


def _build_odbc_connection_string(raw: str) -> str:
    """Always prepend ODBC Driver 18 + encryption; map somee ADO keys if needed."""
    pairs = _parse_key_value_pairs(raw)

    server = (
        pairs.get("server")
        or pairs.get("data source")
        or pairs.get("host")
    )
    database = (
        pairs.get("database")
        or pairs.get("initial catalog")
        or pairs.get("db")
    )
    uid = pairs.get("uid") or pairs.get("user id") or pairs.get("user")
    pwd = pairs.get("pwd") or pairs.get("password")

    missing = [
        name
        for name, value in [
            ("SERVER/data source", server),
            ("DATABASE/initial catalog", database),
            ("UID/user id", uid),
            ("PWD/pwd", pwd),
        ]
        if not value
    ]
    if missing:
        raise ValueError(
            "Could not parse required connection fields from SOMEE_CONNECTION_STRING: "
            + ", ".join(missing)
            + ". Expected ODBC keys (SERVER, DATABASE, UID, PWD) or somee ADO keys "
            "(data source, initial catalog, user id, pwd)."
        )

    return (
        f"DRIVER={ODBC_DRIVER};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={uid};"
        f"PWD={pwd};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )


def _mask_password(conn_str: str) -> str:
    return re.sub(r"(PWD=)([^;]*)", r"\1***", conn_str, flags=re.IGNORECASE)


def _ensure_table(cursor: pyodbc.Cursor) -> None:
    cursor.execute(
        f"""
        IF NOT EXISTS (
            SELECT 1 FROM sys.tables WHERE name = '{TABLE_NAME}'
        )
        BEGIN
            CREATE TABLE {TABLE_NAME} (
                id INT IDENTITY(1,1) PRIMARY KEY,
                note NVARCHAR(200) NOT NULL,
                created_at DATETIME NOT NULL
            );
        END
        """
    )


def main() -> int:
    # 1) Read from .env (raw somee string — may be ADO-style without DRIVER=)
    raw_env = _load_raw_env_value()

    try:
        conn_str = _build_odbc_connection_string(raw_env)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    # 2) Connect — print masked final ODBC string immediately before connect
    print("Connecting to somee.com MS SQL…")
    print(f"Final ODBC connection string: {_mask_password(conn_str)}")

    try:
        conn = pyodbc.connect(conn_str, timeout=30)
    except pyodbc.Error as exc:
        print(
            "FAIL: Could not connect.\n"
            f"  {exc}\n\n"
            "Checklist:\n"
            "  - SERVER/data source and DATABASE/initial catalog are correct\n"
            "  - UID/user id and PWD/pwd are correct\n"
            "  - ODBC Driver 18 for SQL Server is installed (64-bit for 64-bit Python)\n"
            "  - Outbound TCP 1433 is not blocked",
            file=sys.stderr,
        )
        return 1

    try:
        conn.autocommit = False
        cursor = conn.cursor()

        _ensure_table(cursor)
        conn.commit()
        print(f"Table '{TABLE_NAME}' exists (created if missing).")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cursor.execute(
            f"INSERT INTO {TABLE_NAME} (note, created_at) VALUES (?, ?)",
            (TEST_NOTE, now),
        )
        conn.commit()
        print("Inserted one test row.")

        cursor.execute(
            f"SELECT TOP 1 id, note, created_at FROM {TABLE_NAME} ORDER BY id DESC"
        )
        row = cursor.fetchone()
        if row is None:
            print("FAIL: Insert succeeded but SELECT returned no rows.", file=sys.stderr)
            return 1

        print("\nLatest row from database:")
        print(f"  id         = {row.id}")
        print(f"  note       = {row.note}")
        print(f"  created_at = {row.created_at}")
        print("\nSUCCESS: somee.com connection spike passed.")
        return 0

    except pyodbc.Error as exc:
        conn.rollback()
        print(f"FAIL: Database operation error:\n  {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
