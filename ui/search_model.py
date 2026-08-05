from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    success: bool
    message: str
    flights: list[dict[str, Any]] | None = None
    cache_hit: bool = False


@dataclass
class DetailsResult:
    success: bool
    message: str
    details: dict[str, Any] | None = None


class SearchModel:
    def __init__(self, gateway_base_url: str = "http://127.0.0.1:8000") -> None:
        self._base_url = gateway_base_url.rstrip("/")

    def search(
        self,
        origin: str,
        destination: str,
        date: str,
        access_token: str,
    ) -> SearchResult:
        url = f"{self._base_url}/flights/search"
        params = {
            "origin": origin.strip().upper(),
            "destination": destination.strip().upper(),
            "date": date,
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        logger.info("GET %s params=%s", url, params)

        try:
            response = httpx.get(url, params=params, headers=headers, timeout=60.0)
        except httpx.RequestError as exc:
            logger.exception("Search network error")
            return SearchResult(success=False, message=f"Network error: {exc}")

        logger.info("Search response status=%s", response.status_code)

        if response.status_code == 200:
            data = response.json()
            return SearchResult(
                success=True,
                message="OK",
                flights=data.get("flights") or [],
                cache_hit=bool(data.get("cache_hit")),
            )

        if response.status_code == 401:
            return SearchResult(
                success=False,
                message="Session expired or invalid. Please log in again.",
            )

        return SearchResult(success=False, message=_extract_detail(response))

    def get_flight_details(self, flight_id: str, access_token: str) -> DetailsResult:
        encoded = quote(flight_id, safe="")
        url = f"{self._base_url}/flights/{encoded}"
        headers = {"Authorization": f"Bearer {access_token}"}
        logger.info("GET %s", url)

        try:
            response = httpx.get(url, headers=headers, timeout=30.0)
        except httpx.RequestError as exc:
            logger.exception("Details network error")
            return DetailsResult(success=False, message=f"Network error: {exc}")

        logger.info("Details response status=%s", response.status_code)

        if response.status_code == 200:
            return DetailsResult(success=True, message="OK", details=response.json())

        if response.status_code == 401:
            return DetailsResult(
                success=False,
                message="Session expired or invalid. Please log in again.",
            )

        if response.status_code == 404:
            return DetailsResult(success=False, message=_extract_detail(response))

        return DetailsResult(success=False, message=_extract_detail(response))


def _extract_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"Request failed (HTTP {response.status_code})."

    detail = payload.get("detail", payload)
    if isinstance(detail, list):
        return "; ".join(str(item) for item in detail)
    return str(detail)
