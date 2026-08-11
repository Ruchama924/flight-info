# Gateway — Slice 1 (Auth) + Slice 2 (Flight search proxy)

FastAPI gateway that forwards requests to the app-server.

## Setup

```powershell
cd gateway
py -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

> On Windows, use `py` (not `python`) to create the venv — the global
> `python` command may be an empty App Execution Alias stub.

## Run

Start the **app-server first** (port 8001), then:

```powershell
.\.venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8000 --reload
```

Health check: http://127.0.0.1:8000/health

## Proxied endpoints

| Method | Path | Forwards to |
|--------|------|-------------|
| POST | `/auth/register` | app-server `/auth/register` |
| POST | `/auth/login` | app-server `/auth/login` |
| GET | `/flights/search` | app-server `/flights/search` (forwards `Authorization`) |
| GET | `/flights/{flight_id}` | app-server `/flights/{flight_id}` (forwards `Authorization`) |
| POST | `/advisor/ask` | app-server `/advisor/ask` (forwards `Authorization`) |

## Optional environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_SERVER_URL` | `http://127.0.0.1:8001` | Upstream app-server base URL |
