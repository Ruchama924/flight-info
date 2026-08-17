from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


@dataclass
class CreateBookingResult:
    success: bool
    message: str
    booking: dict[str, Any] | None = None


@dataclass
class MyBookingsResult:
    success: bool
    message: str
    bookings: list[dict[str, Any]] | None = None


@dataclass
class CancelBookingResult:
    success: bool
    message: str


class BookingModel:
    def __init__(self, gateway_base_url: str = "http://127.0.0.1:8000") -> None:
        self._base_url = gateway_base_url.rstrip("/")

    def create_booking(
        self,
        flight_id: str,
        passenger_name: str,
        passport_number: str,
        access_token: str,
    ) -> CreateBookingResult:
        url = f"{self._base_url}/bookings"
        headers = {"Authorization": f"Bearer {access_token}"}
        body = {
            "flight_id": flight_id,
            "passenger_name": passenger_name,
            "passport_number": passport_number,
        }
        logger.info("POST %s flight_id=%s", url, flight_id)

        try:
            response = httpx.post(url, json=body, headers=headers, timeout=30.0)
        except httpx.RequestError as exc:
            logger.exception("Create booking network error")
            return CreateBookingResult(success=False, message=f"Network error: {exc}")

        logger.info("Create booking response status=%s", response.status_code)

        if response.status_code == 200:
            return CreateBookingResult(
                success=True,
                message="Booking created.",
                booking=response.json(),
            )

        if response.status_code == 401:
            return CreateBookingResult(
                success=False,
                message="Session expired or invalid. Please log in again.",
            )

        return CreateBookingResult(success=False, message=_extract_detail(response))

    def get_my_bookings(self, access_token: str) -> MyBookingsResult:
        url = f"{self._base_url}/bookings/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        logger.info("GET %s", url)

        try:
            response = httpx.get(url, headers=headers, timeout=30.0)
        except httpx.RequestError as exc:
            logger.exception("My bookings network error")
            return MyBookingsResult(success=False, message=f"Network error: {exc}")

        logger.info("My bookings response status=%s", response.status_code)

        if response.status_code == 200:
            data = response.json()
            return MyBookingsResult(
                success=True,
                message="OK",
                bookings=list(data.get("bookings") or []),
            )

        if response.status_code == 401:
            return MyBookingsResult(
                success=False,
                message="Session expired or invalid. Please log in again.",
            )

        return MyBookingsResult(success=False, message=_extract_detail(response))

    def cancel_booking(self, booking_id: str, access_token: str) -> CancelBookingResult:
        encoded = quote(booking_id, safe="")
        url = f"{self._base_url}/bookings/{encoded}"
        headers = {"Authorization": f"Bearer {access_token}"}
        logger.info("DELETE %s", url)

        try:
            response = httpx.delete(url, headers=headers, timeout=30.0)
        except httpx.RequestError as exc:
            logger.exception("Cancel booking network error")
            return CancelBookingResult(success=False, message=f"Network error: {exc}")

        logger.info("Cancel booking response status=%s", response.status_code)

        if response.status_code == 200:
            return CancelBookingResult(success=True, message="Booking cancelled.")

        if response.status_code == 401:
            return CancelBookingResult(
                success=False,
                message="Session expired or invalid. Please log in again.",
            )

        return CancelBookingResult(success=False, message=_extract_detail(response))


def _extract_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"Request failed (HTTP {response.status_code})."

    detail = payload.get("detail", payload)
    if isinstance(detail, list):
        return "; ".join(str(item) for item in detail)
    return str(detail)
