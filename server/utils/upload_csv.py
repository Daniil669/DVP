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

def _extract_parent_from_path(path: str, child: str) -> str:
    """Extract parent from path string.
    Two cases in the data:
    1. Path includes child: '->MODMAT000001->MAT000121' where child='MAT000121'
       → parent is second-to-last element
    2. Path excludes child: '->MODMAT000001->MAT000121->MAT003121' where child='MAT000122'
       → parent is last element (child is one level deeper than path shows)
    """
    parts = [p.strip() for p in path.split('->') if p.strip()]
    
    if not parts:
        return child
    
    # Check if last element in path matches the child
    if len(parts) >= 2 and parts[-1] == child:
        return parts[-2]
    else:
        return parts[-1]

def _parse_csv_text(text: str) -> pd.DataFrame:
    """Auto-detect delimiter (',' or ';') and validate required headers."""
    df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
    df.columns = _normalize_cols(df.columns)
    
    new_format = ["eng_id", "child_item_id", "path", "chain_sort", "sequenceno"]
    old_format = ["parent_item", "child_item", "sequence_no", "level"]
    
    has_new = all(c in df.columns for c in new_format)
    has_old = all(c in df.columns for c in old_format)
    
    if has_new:
        # Drop rows with missing critical values (only path needed now)
        df = df.dropna(subset=['path', 'chain_sort', 'sequenceno'])
        
        # Keep the original path column for processing
        df['path'] = df['path'].astype(str)
        df['chain_sort'] = pd.to_numeric(df['chain_sort'], errors='coerce').fillna(1).astype(int)
        df['sequenceno'] = pd.to_numeric(df['sequenceno'], errors='coerce').fillna(0).astype(int)
        
    elif not has_old:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns. Expected either {old_format} or {new_format}. Found: {list(df.columns)}"
        ) 
    return df

def _load_df_into_store(df: pd.DataFrame) -> int:
    clear_data()
    added_relationships = {}  # Track: (parent, child) -> (sequence, level)
    
    for _, row in df.iterrows():
        # If this row has a 'path' column (new format), extract all relationships from path
        if 'path' in row.index and pd.notna(row['path']):
            path_str = str(row['path'])
            parts = [p.strip() for p in path_str.split('->') if p.strip()]
            child_item_id = str(row.get('child_item_id', '')).strip()
            
            if not parts:
                continue
            
            # Extract relationships from consecutive pairs in path
            for i in range(len(parts) - 1):
                parent = parts[i]
                child = parts[i + 1]
                rel_key = (parent, child)
                
                # For the LAST pair in the path, use actual chain_sort and sequenceno
                if i == len(parts) - 2:  # Last pair
                    level = int(row.get('chain_sort', i + 1))
                    sequence = int(row.get('sequenceno', 0))
                else:
                    # For intermediate pairs, use default values
                    level = i + 1
                    sequence = 0
                
                # Only add if not exists, or update if this has better info (non-zero sequence)
                if rel_key not in added_relationships or (sequence > 0 and added_relationships[rel_key][0] == 0):
                    added_relationships[rel_key] = (sequence, level)
            
            # ========== ADDED: Handle child_item_id if different from last node ==========
            # If child_item_id exists and is different from the last node in path, add that relationship
            if child_item_id and parts and parts[-1] != child_item_id:
                parent = parts[-1]
                child = child_item_id
                rel_key = (parent, child)
                level = int(row.get('chain_sort', len(parts))) + 1  # One level deeper
                sequence = int(row.get('sequenceno', 0))
                
                if rel_key not in added_relationships or (sequence > 0 and added_relationships[rel_key][0] == 0):
                    added_relationships[rel_key] = (sequence, level)
        
        # Old format: use parent_item and child_item directly
        elif 'parent_item' in row.index and 'child_item' in row.index:
            parent = str(row["parent_item"])
            child = str(row["child_item"])
            rel_key = (parent, child)
            sequence = int(row.get("sequence_no", 0))
            level = int(row.get("level", 1))
            
            if rel_key not in added_relationships:
                added_relationships[rel_key] = (sequence, level)
    
    # Add all relationships to store
    for (parent, child), (sequence, level) in added_relationships.items():
        add_relationship(
            parent=parent,
            child=child,
            sequence=sequence,
            level=level,
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