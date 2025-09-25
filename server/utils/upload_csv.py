# server/utils/upload_csv.py
from __future__ import annotations
from fastapi import UploadFile, HTTPException
from pathlib import Path
from utils.sample_data import clear_data, add_relationship, get_sample_data
import pandas as pd
import io, re

# ---- config ----
DATA_DIR = (Path(__file__).resolve().parents[1] / "data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---- helpers ----
def _safe_name(name: str) -> str:
    """Sanitize the original filename (keep extension), used as canonical name on disk."""
    base = Path(name).name
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("_")
    return safe or "uploaded.csv"

def _normalize_cols(cols):
    return [str(c).strip().lower().replace("\ufeff", "") for c in cols]

def _parse_csv_text(text: str) -> pd.DataFrame:
    """Auto-detect delimiter (',' or ';') and validate required headers."""
    df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
    df.columns = _normalize_cols(df.columns)
    required = ["parent_item", "child_item", "sequence_no", "level"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {missing}. Found: {list(df.columns)}"
        )
    return df

def _load_df_into_store(df: pd.DataFrame) -> int:
    clear_data()
    for _, row in df.iterrows():
        add_relationship(
            parent=str(row["parent_item"]),
            child=str(row["child_item"]),
            sequence=int(row["sequence_no"]),
            level=int(row["level"]),
        )
    return len(get_sample_data())

# ---- main API ----
async def upload_csv(file: UploadFile):
    """
    Behavior:
    - If a CSV with the same sanitized filename already exists in /data, do NOT overwrite;
      load it from disk and return from_cache=True.
    - Otherwise validate the uploaded content, save as <safe_name>, load it, and return from_cache=False.
    """
    try:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="File must be a CSV")

        safe_name = _safe_name(file.filename)
        save_path = DATA_DIR / safe_name

        # If already on disk -> reuse cached file
        if save_path.exists():
            text = save_path.read_text(encoding="utf-8", errors="replace")
            df = _parse_csv_text(text)
            n = _load_df_into_store(df)
            return {
                "message": "File already existed; loaded from disk",
                "file_name": file.filename,
                "saved_as": save_path.name,
                "saved_path": str(save_path),
                "relationships_loaded": n,
                "success": True,
                "from_cache": True,
            }

        # New file: read, validate, then persist original bytes
        raw = await file.read()
        text = raw.decode("utf-8", errors="replace")
        df = _parse_csv_text(text)  # raises 400 if invalid

        # persist (idempotent canonical name, no timestamp)
        save_path.write_bytes(raw)

        n = _load_df_into_store(df)
        return {
            "message": "CSV uploaded, saved, and loaded",
            "file_name": file.filename,
            "saved_as": save_path.name,
            "saved_path": str(save_path),
            "relationships_loaded": n,
            "success": True,
            "from_cache": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {e}")
