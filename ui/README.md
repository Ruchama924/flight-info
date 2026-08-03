# UI — Slice 1 (Auth) + Slice 2 (Flight search)

PySide6 desktop client using MVP:

- Auth: `LoginView` → `LoginPresenter` → `AuthModel`
- Search: `SearchView` → `SearchPresenter` → `SearchModel`

## Setup

```powershell
cd ui
py -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

> On Windows, use `py` (not `python`) to create the venv — the global
> `python` command may be an empty App Execution Alias stub.

## Run

Start **app-server** (8001) and **gateway** (8000) first, then:

```powershell
.\.venv\Scripts\python.exe main.py
```

## Usage

1. **Register** tab — create an account.
2. **Login** tab — log in (JWT stored in `SessionStore`).
3. **Search Flights** tab — enter IATA codes (e.g. `JFK` → `LAX`), pick a date, click Search.
4. Results appear in the table (airline, flight, departure, arrival, price).

If you search while logged out, you get a clear message to log in first.

The UI talks to the gateway at `http://127.0.0.1:8000`.
