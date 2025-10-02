# FastAPI Server – README (Updated)

This backend accepts a CSV of parent–child relationships **or** serves data from a database connection. It lets you:

- Upload/choose a **CSV** stored on the server and query root/children.
- Register and activate **database** connections (SQLite by default; Postgres supported later).
- List available sources (CSVs + DB connections) and **switch** the active source.
- Query **root node(s)** and **children** from the active source.

---

## 1) Install environment & dependencies

**Prereqs**
- Python **3.11+** (tested with 3.12)
- pip

```bash
# from the server/ directory
python -m venv .venv

# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# upgrade pip (optional)
python -m pip install --upgrade pip

# install dependencies
pip install -r requirements.txt
```

Environment variables (optional):
- `DATABASE_URL`: graph DB URL (default: `sqlite+aiosqlite:///./data/app.db`)
- `REGISTRY_DATABASE_URL`: registry DB URL (default: `sqlite+aiosqlite:///./data/registry.db`)
- `SQL_ECHO=1`: SQLAlchemy echo logs

---

## 2) Run the server locally

From the `server/` directory:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- Swagger UI: `http://localhost:8000/docs`
- CSV uploads and stored CSVs are placed in `server/data/` (auto-created).
- On startup, tables for both the **graph DB** and **registry DB** are created automatically.

**CSV format (required headers):**
```
parent_item,child_item,sequence_no,level
```
- Delimiter: **auto-detected** (`;` or `,` both work)
- Headers are case-insensitive; BOM/whitespace are handled

---

## 3) Sources model

This server can serve data from **one active source** at a time:

- **CSV source**: in-memory dataset loaded from a CSV file under `server/data/*.csv`
- **DB source**: dataset available through the configured graph database connection

A separate **registry database** stores:
- Known DB connections (name, URL, optional API key)
- The **active source** (e.g., `csv:myfile.csv` or `db:3`)

You can switch the active source with `/api/sources/select` (see below).

---

## 4) Endpoints

Base prefix: **`/api`**

### 4.1 List available sources
`GET /api/sources`

Response example:
```json
{
  "csv_files": [
    { "name": "where_used_sample_100_lines_student_version.csv", "size": 12345, "modified_at": 1727820000 }
  ],
  "db_connections": [
    { "id": 1, "name": "local-sqlite", "url": "sqlite+aiosqlite:///./data/app.db", "is_active": true, "has_api_key": true }
  ],
  "active": { "type": "csv", "value": "where_used_sample_100_lines_student_version.csv" }
}
```

---

### 4.2 Select active source (CSV or DB)
`POST /api/sources/select`

**Select a CSV stored on the server:**
```http
POST /api/sources/select
Content-Type: application/json

{
  "type": "csv",
  "filename": "where_used_sample_100_lines_student_version.csv"
}
```
- Loads the CSV into memory and sets it as the active source.

**Select a previously registered DB connection:**
```http
POST /api/sources/select
x-api-key: secret123
Content-Type: application/json

{
  "type": "db",
  "connection_id": 1
}
```
- Switches the graph DB context to this connection.
- If the connection has an `api_key`, you must pass it via `x-api-key` header (simple auth; can be hardened later).

---

### 4.3 Register a DB connection
`POST /api/db/register`

Body:
```json
{
  "name": "local-sqlite",
  "url": "sqlite+aiosqlite:///./data/app.db",
  "api_key": "secret123"
}
```
- Stores the connection in the registry DB (not active by default).

---

### 4.4 Upload CSV & compute roots (optional upload)
`POST /api/root_node`

- If you include a file, it will be validated, saved (idempotent name), loaded, and set as active CSV.
- If you don’t include a file, the endpoint serves the current **active source** (CSV or DB).

**With file (multipart/form-data):**
```bash
curl -X POST "http://localhost:8000/api/root_node" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@where_used_sample_100_lines_student_version.csv"
```
**Without file (use current active source):**
```bash
curl -X POST "http://localhost:8000/api/root_node" -H "accept: application/json"
```

Sample response:
```json
{
  "message": "Root node(s) computed (CSV)",
  "root_nodes": ["MAT000001", "MAT000002"],
  "count": 2
}
```

---

### 4.5 Read-only roots
`GET /api/root_node`

Returns roots from the **active source** (CSV or DB); no upload required.

---

### 4.6 Children of a node (from active source)
`GET /api/child_node?node_id=MAT000001&limit=3`

Response example:
```json
{
  "search_id": "MAT000001",
  "parent": null,
  "children": [
    { "id": "MAT000004", "name": "MAT000004", "sequence_no": 1, "level": 1 },
    { "id": "MAT000007", "name": "MAT000007", "sequence_no": 10, "level": 1 },
    { "id": "MAT000008", "name": "MAT000008", "sequence_no": 11, "level": 1 }
  ],
  "count_children": 3
}
```

---