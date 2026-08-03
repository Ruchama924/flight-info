# UI — Slice 1 (Login / Register)

PySide6 desktop client using MVP: `LoginView` → `LoginPresenter` → `AuthModel` → Gateway.

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

1. Open the **Register** tab, enter email + password (min 6 chars), click Register.
2. Switch to **Login**, enter the same credentials, click Login.
3. On success you should see `Logged in as {email}`. The JWT is stored in memory via `SessionStore` for later slices.

The UI talks to the gateway at `http://127.0.0.1:8000` by default (configured in `auth_model.py`).
