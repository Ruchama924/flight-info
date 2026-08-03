from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class AuthResult:
    success: bool
    message: str
    access_token: str | None = None
    user_id: str | None = None
    email: str | None = None


class AuthModel:
    def __init__(self, gateway_base_url: str = "http://127.0.0.1:8000") -> None:
        self._base_url = gateway_base_url.rstrip("/")

    def register(self, email: str, password: str) -> AuthResult:
        logger.info("AuthModel.register -> POST %s/auth/register", self._base_url)
        try:
            response = httpx.post(
                f"{self._base_url}/auth/register",
                json={"email": email, "password": password},
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            logger.exception("AuthModel.register network error")
            return AuthResult(success=False, message=f"Network error: {exc}")
        except Exception as exc:
            logger.error("ERROR in AuthModel.register:\n%s", traceback.format_exc())
            return AuthResult(success=False, message=f"Unexpected error: {exc}")

        logger.info("AuthModel.register status=%s", response.status_code)
        if response.status_code == 200:
            data = response.json()
            return AuthResult(
                success=True,
                message="Registration successful.",
                user_id=data.get("user_id"),
                email=data.get("email"),
            )

        return AuthResult(success=False, message=_extract_detail(response))

    def login(self, email: str, password: str) -> AuthResult:
        logger.info("AuthModel.login -> POST %s/auth/login", self._base_url)
        try:
            response = httpx.post(
                f"{self._base_url}/auth/login",
                json={"email": email, "password": password},
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            logger.exception("AuthModel.login network error")
            return AuthResult(success=False, message=f"Network error: {exc}")
        except Exception as exc:
            logger.error("ERROR in AuthModel.login:\n%s", traceback.format_exc())
            return AuthResult(success=False, message=f"Unexpected error: {exc}")

        logger.info("AuthModel.login status=%s", response.status_code)
        if response.status_code == 200:
            data = response.json()
            return AuthResult(
                success=True,
                message="Login successful.",
                access_token=data.get("access_token"),
                user_id=data.get("user_id"),
                email=data.get("email"),
            )

        return AuthResult(success=False, message=_extract_detail(response))


def _extract_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"Request failed (HTTP {response.status_code})."

    detail = payload.get("detail", payload)
    if isinstance(detail, list):
        return "; ".join(str(item) for item in detail)
    return str(detail)
