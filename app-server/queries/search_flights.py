from __future__ import annotations

import hashlib
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from models.flight_schemas import FlightSummary

logger = logging.getLogger(__name__)

# AviationStack free tier requires plain HTTP (HTTPS is paid-only).
API_URL = "http://api.aviationstack.com/v1/flights"
CACHE_TTL = timedelta(minutes=10)

# Project-root .env (flight-info/.env), same as external_api_test.py
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_PATH)


@dataclass(frozen=True)
class SearchFlightsQuery:
    origin: str
    destination: str
    date: str  # YYYY-MM-DD


@dataclass
class _CacheEntry:
    flights: list[FlightSummary]
    expires_at: datetime


class ExternalApiError(Exception):
    pass


class SearchFlightsHandler:
    def __init__(self) -> None:
        self._cache: dict[str, _CacheEntry] = {}

    def handle(self, query: SearchFlightsQuery) -> tuple[list[FlightSummary], bool]:
        origin = query.origin.strip().upper()
        destination = query.destination.strip().upper()
        date = query.date.strip()
        cache_key = f"{origin}|{destination}|{date}"

        cached = self._get_fresh_cache(cache_key)
        if cached is not None:
            logger.info("cache hit key=%s flights=%d", cache_key, len(cached))
            return cached, True

        logger.info("cache miss key=%s — calling AviationStack", cache_key)
        flights = self._fetch_and_map(origin, destination, date)
        self._cache[cache_key] = _CacheEntry(
            flights=flights,
            expires_at=datetime.now(timezone.utc) + CACHE_TTL,
        )
        return flights, False

    def _get_fresh_cache(self, key: str) -> list[FlightSummary] | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        if datetime.now(timezone.utc) >= entry.expires_at:
            del self._cache[key]
            return None
        return entry.flights

    def _fetch_and_map(
        self, origin: str, destination: str, date: str
    ) -> list[FlightSummary]:
        api_key = os.getenv("FLIGHT_API_KEY", "").strip()
        if not api_key:
            raise ExternalApiError(
                "FLIGHT_API_KEY is missing. Set it in the project-root .env file."
            )

        raw = self._call_aviationstack(api_key, origin, destination, date)
        if isinstance(raw, dict) and raw.get("error"):
            raise ExternalApiError(str(raw["error"]))

        items = raw.get("data") if isinstance(raw, dict) else None
        if not isinstance(items, list):
            raise ExternalApiError("Unexpected AviationStack response shape.")

        flights: list[FlightSummary] = []
        for item in items:
            summary = self._to_summary(item, origin, destination, date)
            if summary is not None:
                flights.append(summary)
        return flights

    def _call_aviationstack(
        self, api_key: str, origin: str, destination: str, date: str
    ) -> dict[str, Any]:
        """Call AviationStack; fall back if free-tier rejects filter params."""
        filtered_params = {
            "access_key": api_key,
            "dep_iata": origin,
            "arr_iata": destination,
            "flight_date": date,
            "limit": 20,
        }
        try:
            return self._http_get(filtered_params)
        except ExternalApiError as exc:
            logger.warning(
                "AviationStack filtered request failed (%s); "
                "falling back to unfiltered fetch + local filter (free-tier).",
                exc,
            )

        # Free tier often rejects dep_iata/arr_iata/flight_date — same base
        # pattern as external_api_test.py, then filter client-side.
        broad = self._http_get({"access_key": api_key, "limit": 100})
        items = broad.get("data") if isinstance(broad, dict) else None
        if not isinstance(items, list):
            return broad

        filtered = [
            item
            for item in items
            if self._matches_route(item, origin, destination, date)
        ]
        if filtered:
            logger.info(
                "Local filter kept %d/%d flights for %s→%s on %s",
                len(filtered),
                len(items),
                origin,
                destination,
                date,
            )
            return {**broad, "data": filtered}

        # Free-tier sample is global/random — exact route match is often empty.
        # Return a capped sample so the UI remains testable; prices stay mocked.
        logger.warning(
            "No exact %s→%s/%s matches in free-tier sample; "
            "returning up to 20 live flights (route filter unavailable).",
            origin,
            destination,
            date,
        )
        return {**broad, "data": items[:20]}

    def _http_get(self, params: dict[str, Any]) -> dict[str, Any]:
        query = urllib.parse.urlencode(params)
        url = f"{API_URL}?{query}"
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise ExternalApiError(f"HTTP {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise ExternalApiError(f"Request failed: {exc.reason}") from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ExternalApiError("AviationStack returned non-JSON body.") from exc

        if isinstance(parsed, dict) and parsed.get("error"):
            raise ExternalApiError(str(parsed["error"]))
        return parsed if isinstance(parsed, dict) else {"data": []}

    @staticmethod
    def _matches_route(
        item: dict[str, Any], origin: str, destination: str, date: str
    ) -> bool:
        dep = (item.get("departure") or {}).get("iata") or ""
        arr = (item.get("arrival") or {}).get("iata") or ""
        flight_date = item.get("flight_date") or ""
        if dep.upper() != origin or arr.upper() != destination:
            return False
        # If date is present on the payload, require a match; otherwise keep.
        if flight_date and flight_date != date:
            return False
        return True

    def _to_summary(
        self,
        item: dict[str, Any],
        fallback_origin: str,
        fallback_destination: str,
        fallback_date: str,
    ) -> FlightSummary | None:
        airline = (item.get("airline") or {}).get("name") or "Unknown airline"
        flight = item.get("flight") or {}
        flight_iata = flight.get("iata") or flight.get("number") or ""
        if not flight_iata:
            return None

        departure = item.get("departure") or {}
        arrival = item.get("arrival") or {}
        origin = (departure.get("iata") or fallback_origin).upper()
        destination = (arrival.get("iata") or fallback_destination).upper()

        # Prefer live schedule fields; fall back to flight_date.
        departure_time = departure.get("scheduled") or item.get("flight_date") or fallback_date
        arrival_time = arrival.get("scheduled")

        # AviationStack free tier typically has no commercial fare data.
        # Placeholder: deterministic mock price from flight number so charts
        # (Slice 3) have stable numbers. Same flight_id => same price.
        price = _mock_price_from_flight_id(str(flight_iata))

        stops = 0
        if item.get("flight", {}).get("codeshared"):
            stops = 1

        return FlightSummary(
            flight_id=str(flight_iata),
            airline=str(airline),
            origin=origin,
            destination=destination,
            departure_time=str(departure_time) if departure_time else None,
            arrival_time=str(arrival_time) if arrival_time else None,
            price=price,
            stops=stops,
        )


def _mock_price_from_flight_id(flight_id: str) -> float:
    """Deterministic placeholder USD price for free-tier (no real fares)."""
    digest = hashlib.sha256(flight_id.encode("utf-8")).hexdigest()
    # Map to a plausible range: $89 – $899
    bucket = int(digest[:8], 16) % 811
    return float(89 + bucket)
