# App Server — Slice 1 (Auth)

FastAPI application server with CQRS-style commands/queries and SQLite event store.

## Setup

```powershell
cd app-server
py -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

> On Windows, use `py` (not `python`) to create the venv — the global
> `python` command may be an empty App Execution Alias stub.

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
| GET | `/health` | Service health |

## Optional environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | dev secret | Signing key for JWT tokens |
| `JWT_EXPIRE_MINUTES` | `60` | Token lifetime |

## Manual test (curl)

```powershell
curl -X POST http://127.0.0.1:8001/auth/register -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\",\"password\":\"secret123\"}"

curl -X POST http://127.0.0.1:8001/auth/login -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\",\"password\":\"secret123\"}"
```
