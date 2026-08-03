"""Slice 0 smoke test — one request to AviationStack using FLIGHT_API_KEY from .env.

Run on Windows:  py external_api_test.py
(with python-dotenv installed in your venv or globally via py -m pip)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

# AviationStack free tier requires plain HTTP (HTTPS is paid-only).
API_URL = "http://api.aviationstack.com/v1/flights"


def main() -> int:
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("FLIGHT_API_KEY", "").strip()
    if not api_key:
        print(
            "Error: FLIGHT_API_KEY is missing.\n"
            f"Copy .env.example to .env in {env_path.parent} and set your key.",
            file=sys.stderr,
        )
        return 1

    # Free plan: no extra query params; limit response size for a quick check.
    url = f"{API_URL}?access_key={api_key}&limit=1"
    request = urllib.request.Request(url, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"Error: AviationStack returned HTTP {exc.code}.", file=sys.stderr)
        print(error_body, file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Error: Request failed — {exc.reason}", file=sys.stderr)
        return 1

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        print(body)
        return 0

    if isinstance(parsed, dict) and parsed.get("error"):
        print("Error: AviationStack returned an error response:", file=sys.stderr)
        print(json.dumps(parsed, indent=2))
        return 1

    print(json.dumps(parsed, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
