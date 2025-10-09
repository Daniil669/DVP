# server/utils/csv_import.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd, io, hashlib, re
from fastapi import HTTPException

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _normalize_cols(cols):
    return [str(c).strip().lower().replace("\ufeff", "") for c in cols]

def parse_csv_text(text: str) -> List[Dict]:
    df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
    df.columns = _normalize_cols(df.columns)
    required = ["parent_item", "child_item", "sequence_no", "level"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {missing}. Found: {list(df.columns)}")
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "parent_item": str(r["parent_item"]),
            "child_item":  str(r["child_item"]),
            "sequence_no": int(r["sequence_no"]),
            "level":       int(r["level"]),
        })
    return rows

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def save_bytes_unique(name: str, raw: bytes) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).name) or "uploaded.csv"
    p = DATA_DIR / safe
    if not p.exists():
        p.write_bytes(raw)
    return p

def read_server_csv(filename: str) -> Tuple[str, List[Dict], Path]:
    p = DATA_DIR / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"CSV not found on server: {filename}")
    raw = p.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    rows = parse_csv_text(text)
    return sha256_bytes(raw), rows, p
