from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    success: bool
    message: str
    flights: list[dict[str, Any]] | None = None
    cache_hit: bool = False


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


def _extract_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"Request failed (HTTP {response.status_code})."

    detail = payload.get("detail", payload)
    if isinstance(detail, list):
        return "; ".join(str(item) for item in detail)
    return str(detail)
