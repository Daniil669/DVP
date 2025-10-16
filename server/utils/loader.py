# server/utils/loader.py
from __future__ import annotations
from pathlib import Path
from fastapi import HTTPException
from utils.sample_data import clear_data, add_relationship, get_sample_data
import pandas as pd, io

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def list_csv_files() -> list[dict]:
    out = []
    for p in sorted(DATA_DIR.glob("*.csv"), key=lambda x: x.stat().st_mtime, reverse=True):
        st = p.stat()
        out.append({"name": p.name, "size": st.st_size, "modified_at": int(st.st_mtime)})
    return out

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
        return child  # fallback
    
    # Check if last element in path matches the child
    if len(parts) >= 2 and parts[-1] == child:
        return parts[-2]
    else:
        return parts[-1]

def _parse_csv_text(text: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
    df.columns = _normalize_cols(df.columns)
    
    # Check for new format columns
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

def load_csv_file(path: Path) -> int:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"CSV not found: {path.name}")
    text = path.read_text(encoding="utf-8", errors="replace")
    df = _parse_csv_text(text)
    clear_data()

    added_relationships = {}  # Track: (parent, child) -> (sequence, level)
    
    for _, row in df.iterrows():
        # If this row has a 'path' column (new format), extract all relationships from path
        if 'path' in row.index and pd.notna(row['path']):
            path_str = str(row['path'])
            parts = [p.strip() for p in path_str.split('->') if p.strip()]
            
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
                    # For intermediate pairs, use default values or better ones if already stored
                    level = i + 1
                    sequence = 0
                
                # Only add if not exists, or update if this has better info (non-zero sequence)
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

def latest_csv() -> Path | None:
    files = sorted(DATA_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None

def ensure_data_loaded() -> dict:
    if get_sample_data():
        return {"loaded": False, "reason": "already_in_memory"}
    p = latest_csv()
    if not p:
        raise HTTPException(status_code=404, detail="No CSV loaded and no files found in /data")
    n = load_csv_file(p)
    return {"loaded": True, "from_file": p.name, "relationships": n}