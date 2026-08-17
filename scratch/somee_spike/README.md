# somee.com connection spike (isolated)

Standalone proof that **this Windows machine** can connect to a free
somee.com MS SQL database from Python. This folder is **not** wired into
`app-server/` — use it only to validate connectivity before migrating the
real Event Store.

## 1. Sign up and create a free MS SQL database

1. Go to [https://somee.com](https://somee.com) and create a free account.
2. Log in to the **control panel**.
3. Open the **MS SQL** section.
4. Create a **new database** (free tier is SQL Server–based).
5. Wait until deployment finishes and the database shows as active.

## 2. Get connection credentials

1. In **MS SQL**, click your database name.
2. Open the **Database details** tab.
3. In **Connection details**, find **Connection string**.
4. Click **Copy to clipboard** — this is the string somee.com expects for
   remote clients (ODBC-style).

Typical shape (values will differ):

```text
DRIVER={ODBC Driver 17 for SQL Server};SERVER=yourname.mssql.somee.com;DATABASE=yourname;UID=yourname;PWD=your_password
```

5. Paste it into `scratch/somee_spike/.env` as `SOMEE_CONNECTION_STRING=...`
   (see `.env.example`).

## 3. Firewall / whitelisting / local prerequisites

**On somee.com**

- Remote access depends on your **hosting plan** — check their docs if
  connection fails from outside their network.
- There is usually **no IP whitelist UI** on the free tier; if your plan
  supports remote tools (SSMS), the server is reachable on the host/port in
  the connection string (typically **TCP 1433**).

**On your Windows PC**

- Allow outbound TCP to the somee server (corporate firewalls sometimes block
  1433).
- Install a Microsoft **ODBC Driver for SQL Server** (17 or 18) if you use
  `pyodbc` — see [Microsoft ODBC download](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).
- If the driver name in your string does not match an installed driver, edit
  the `DRIVER={...}` part to match (e.g. `{ODBC Driver 18 for SQL Server}`).

**ODBC Driver 18 note:** it enables encryption by default. If you see SSL
errors against somee, add to the connection string:

```text
Encrypt=yes;TrustServerCertificate=yes
```

## 4. Run the spike

```powershell
cd scratch\somee_spike
copy .env.example .env
# Edit .env and paste your real SOMEE_CONNECTION_STRING

py -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\python.exe test_connection.py
```

**Success:** prints the inserted test row and `SUCCESS: somee.com connection spike passed.`

**Failure:** prints a clear error (missing env, driver not found, login failed,
timeout, etc.).

## 5. What this proves

- Python on this machine can reach somee.com.
- We can create a table and read/write rows (similar shape to a future Event
  Store table: `id`, text payload field, `created_at`).

Do **not** point the main app at somee until a later migration slice replaces
`SQLiteEventStore` behind the repository interface.
