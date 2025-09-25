# server/utils/loader.py
from __future__ import annotations
from pathlib import Path
from fastapi import HTTPException
from utils.sample_data import clear_data, add_relationship, get_sample_data
import pandas as pd
import io, re

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _normalize_cols(cols):
    return [str(c).strip().lower().replace("\ufeff", "") for c in cols]

def _parse_csv_text(text: str) -> pd.DataFrame:
    # auto-detect delimiter, handle BOM/whitespace in headers
    df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
    df.columns = _normalize_cols(df.columns)
    required = ["parent_item", "child_item", "sequence_no", "level"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {missing}. Found: {list(df.columns)}")
    return df

def load_csv_file(path: Path) -> int:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"CSV not found: {path.name}")
    text = path.read_text(encoding="utf-8", errors="replace")
    df = _parse_csv_text(text)

    clear_data()
    for _, row in df.iterrows():
        add_relationship(
            parent=str(row["parent_item"]),
            child=str(row["child_item"]),
            sequence=int(row["sequence_no"]),
            level=int(row["level"]),
        )
    return len(get_sample_data())

def latest_csv() -> Path | None:
    files = sorted(DATA_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None

def ensure_data_loaded() -> dict:
    """If in-memory store is empty, try loading the newest CSV from /data."""
    if get_sample_data():
        return {"loaded": False, "reason": "already_in_memory"}
    p = latest_csv()
    if not p:
        raise HTTPException(status_code=404, detail="No CSV loaded and no files found in /data")
    n = load_csv_file(p)
    return {"loaded": True, "from_file": p.name, "relationships": n}
