from __future__ import annotations

import traceback
from dataclasses import dataclass

import httpx


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
        print(f"AuthModel.register -> POST {self._base_url}/auth/register")
        try:
            response = httpx.post(
                f"{self._base_url}/auth/register",
                json={"email": email, "password": password},
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            print(f"AuthModel.register network error: {exc}")
            traceback.print_exc()
            return AuthResult(success=False, message=f"Network error: {exc}")
        except Exception as exc:
            print("ERROR in AuthModel.register:")
            traceback.print_exc()
            return AuthResult(success=False, message=f"Unexpected error: {exc}")

        print(f"AuthModel.register status={response.status_code}")
        if response.status_code == 200:
            data = response.json()
            return AuthResult(
                success=True,
                message="Registration successful.",
                user_id=data.get("user_id"),
                email=data.get("email"),
            )

        detail = _extract_detail(response)
        return AuthResult(success=False, message=detail)

    def login(self, email: str, password: str) -> AuthResult:
        print(f"AuthModel.login -> POST {self._base_url}/auth/login")
        try:
            response = httpx.post(
                f"{self._base_url}/auth/login",
                json={"email": email, "password": password},
                timeout=30.0,
            )
        except httpx.RequestError as exc:
            print(f"AuthModel.login network error: {exc}")
            traceback.print_exc()
            return AuthResult(success=False, message=f"Network error: {exc}")
        except Exception as exc:
            print("ERROR in AuthModel.login:")
            traceback.print_exc()
            return AuthResult(success=False, message=f"Unexpected error: {exc}")

        print(f"AuthModel.login status={response.status_code}")
        if response.status_code == 200:
            data = response.json()
            return AuthResult(
                success=True,
                message="Login successful.",
                access_token=data.get("access_token"),
                user_id=data.get("user_id"),
                email=data.get("email"),
            )

        detail = _extract_detail(response)
        return AuthResult(success=False, message=detail)


def _extract_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"Request failed (HTTP {response.status_code})."

    detail = payload.get("detail", payload)
    if isinstance(detail, list):
        return "; ".join(str(item) for item in detail)
    return str(detail)
