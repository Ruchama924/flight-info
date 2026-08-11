from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class AskResult:
    success: bool
    message: str
    answer: str | None = None
    topics_used: list[str] | None = None


class AdvisorModel:
    def __init__(self, gateway_base_url: str = "http://127.0.0.1:8000") -> None:
        self._base_url = gateway_base_url.rstrip("/")

    def ask(self, question: str, access_token: str) -> AskResult:
        url = f"{self._base_url}/advisor/ask"
        headers = {"Authorization": f"Bearer {access_token}"}
        logger.info("POST %s question=%r", url, question[:80])

        try:
            response = httpx.post(
                url,
                json={"question": question},
                headers=headers,
                timeout=90.0,
            )
        except httpx.RequestError as exc:
            logger.exception("Advisor network error")
            return AskResult(success=False, message=f"Network error: {exc}")

        logger.info("Advisor response status=%s", response.status_code)

        if response.status_code == 200:
            data = response.json()
            return AskResult(
                success=True,
                message="OK",
                answer=data.get("answer") or "",
                topics_used=list(data.get("topics_used") or []),
            )

        if response.status_code == 401:
            return AskResult(
                success=False,
                message="Session expired or invalid. Please log in again.",
            )

        return AskResult(success=False, message=_extract_detail(response))


def _extract_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"Request failed (HTTP {response.status_code})."

    detail = payload.get("detail", payload)
    if isinstance(detail, list):
        return "; ".join(str(item) for item in detail)
    return str(detail)
