# UI — Slice 1–3 (Auth + Search + Details/Chart)

PySide6 desktop client using MVP:

- Auth: `LoginView` → `LoginPresenter` → `AuthModel`
- Search: `SearchView` → `SearchPresenter` → `SearchModel`
- Details: `FlightDetailsView` (dialog) → `FlightDetailsPresenter`
- Chart: price bar chart embedded under the search results table

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

1. **Register** / **Login** — JWT stored in `SessionStore`.
2. **Search Flights** — e.g. `JFK` → `LAX`, today's date, click Search.
3. Price chart under the table updates automatically (one bar per flight).
4. Select a row and click **Details**, or **double-click** a row — dialog shows
   terminals, gates, delays, aircraft, and codeshare ("Operated by…") when present.

The UI talks to the gateway at `http://127.0.0.1:8000`.
