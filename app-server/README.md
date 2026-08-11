# App Server — Slice 1 (Auth) + Slice 2 (Flight search)

FastAPI application server with CQRS-style commands/queries and SQLite event store.

## Setup

```powershell
cd app-server
py -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

> On Windows, use `py` (not `python`) to create the venv — the global
> `python` command may be an empty App Execution Alias stub.

Requires project-root `.env` with `FLIGHT_API_KEY` (same as Slice 0).

## Run

```powershell
.\.venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8001 --reload
```

Health check: http://127.0.0.1:8001/health

Events are persisted to `data/events.db` (SQLite). To reset auth data, stop the server and delete that file.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register a new user (`email`, `password`) |
| POST | `/auth/login` | Login and receive JWT |
| GET | `/flights/search?origin=&destination=&date=` | Search flights (JWT required) |
| GET | `/flights/{flight_id}` | Flight details from search cache (JWT) |
| POST | `/advisor/ask` | RAG flight advisor (JWT; body `{"question":"..."}`) |
| GET | `/health` | Service health |

Search responses are cached in memory for ~10 minutes (keyed by origin+destination+date). Details reuse that cache — run a search first, then open details. Watch the app-server logs for `cache hit` / `cache miss`.

## Optional environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | dev secret | Signing key for JWT tokens |
| `JWT_EXPIRE_MINUTES` | `60` | Token lifetime |
| `FLIGHT_API_KEY` | (from `.env`) | AviationStack access key |

## Manual test (PowerShell)

```powershell
$body = '{"email":"test@example.com","password":"secret123"}'
$login = Invoke-RestMethod -Uri http://127.0.0.1:8001/auth/login -Method POST -ContentType 'application/json' -Body $body
$token = $login.access_token
Invoke-RestMethod -Uri "http://127.0.0.1:8001/flights/search?origin=JFK&destination=LAX&date=2026-08-03" -Headers @{ Authorization = "Bearer $token" }
```
