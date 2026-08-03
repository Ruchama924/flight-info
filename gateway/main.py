import os

import httpx
from fastapi import FastAPI, HTTPException, Request, Response

APP_SERVER_URL = os.getenv("APP_SERVER_URL", "http://127.0.0.1:8001")

app = FastAPI(title="FlightAdvisor Gateway", version="0.1.0")


async def _forward(request: Request, path: str) -> Response:
    url = f"{APP_SERVER_URL}{path}"
    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream = await client.request(
                method=request.method,
                url=url,
                content=body,
                headers={"Content-Type": "application/json"},
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"App server unavailable: {exc}",
        ) from exc

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


@app.post("/auth/register")
async def register(request: Request) -> Response:
    return await _forward(request, "/auth/register")


@app.post("/auth/login")
async def login(request: Request) -> Response:
    return await _forward(request, "/auth/login")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "gateway"}
