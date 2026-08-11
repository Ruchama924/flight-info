# UI — Slice 1–4 (Auth + Search + Details/Chart + Advisor)

PySide6 desktop client using MVP:

- Auth: `LoginView` → `LoginPresenter` → `AuthModel`
- Search: `SearchView` → `SearchPresenter` → `SearchModel`
- Details: `FlightDetailsView` (dialog) → `FlightDetailsPresenter`
- Chart: price bar chart under the search results table
- Advisor: `AdvisorView` → `AdvisorPresenter` → `AdvisorModel` (HTTP on a background `QThread`)

## Setup

```powershell
cd ui
py -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

> On Windows, use `py` (not `python`) to create the venv — the global
> `python` command may be an empty App Execution Alias stub.

## Run

Start **Ollama**, run **rag/ingest.py** once, then **app-server** (8001) and
**gateway** (8000), then:

```powershell
.\.venv\Scripts\python.exe main.py
```

## Usage

1. **Register** / **Login** — JWT stored in `SessionStore`.
2. **Search Flights** — search, chart, details (as in Slice 2–3).
3. **Ask Advisor** — type a question, click Ask. Status shows `Thinking…`
   while the local LLM answers; the window stays responsive. The answer lists
   which knowledge topics were used.

The UI talks to the gateway at `http://127.0.0.1:8000`.
