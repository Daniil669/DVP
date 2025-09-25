# FastAPI Server – README

A small FastAPI backend that accepts a CSV of parent–child relationships, saves the file locally, loads it into memory, and exposes endpoints to fetch **root node(s)** and the **children of a node**.

---

## 1) Install environment & dependencies

**Prereqs**
- Python **3.11+** (tested with 3.12)
- pip

```bash
# from the server/ directory (or cd server)
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

---

## 2) Run the server locally

### Just use command: python main.py

From the `server/` directory:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- Swagger UI: `http://localhost:8000/docs`
- Uploaded CSVs are saved to `server/data/` (auto-created).

**CSV format (required headers):**
```
parent_item,child_item,sequence_no,level
```
- Delimiter: **auto-detected** (`;` or `,` supported)
- Headers are case-insensitive; BOM/whitespace are handled

---

## 3) Endpoints

Base prefix: **`/api`**

### 3.1 `POST /api/root_node`

Upload a CSV, save it to `data/`, load it into memory, and return the **root node(s)** (parents that never appear as children).

**Request (multipart/form-data):**
- `file`: the `.csv` file

**cURL**
```bash
curl -X POST "http://localhost:8000/api/root_node"   -H "accept: application/json"   -H "Content-Type: multipart/form-data"   -F "file=@where_used.csv"
```

**Sample response**
```json
{
  "message": "Root node(s) computed",
  "saved_file": "20250925-112233-where_used.csv",
  "root_nodes": ["MAT000001", "MAT000002"],
  "count": 2
}
```

---

### 3.2 `GET /api/child_node`

Return the **children** of a given node, ordered by `sequence_no`. Optionally limit how many children to return.

**Query params**
- `node_id` (required): the parent node whose children to fetch
- `limit` (optional, int ≥ 1): maximum number of children to return

**Examples**
```bash
# all children
curl "http://localhost:8000/api/child_node?node_id=MAT000001"

# first 3 children
curl "http://localhost:8000/api/child_node?node_id=MAT000001&limit=3"
```

**Sample response**
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

If `node_id` does not exist:
```json
{ "error": "Node XYZ not found", "children": [], "count_children": 0 }
```

---

## Notes & Tips

- CORS is open for development (`allow_origins=["*"]`).
- Each CSV upload **replaces** the in-memory store.
- Check server logs for the exact saved file name in `server/data/`.
