# server/utils/csv_import.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Tuple, Iterable, Optional
import pandas as pd, io, hashlib, re, numpy as np
from fastapi import HTTPException

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _normalize_cols(cols):
    return [str(c).strip().lower().replace("\ufeff", "") for c in cols]

def _sniff_delimiter(sample: str) -> str:
    commas = sample.count(",")
    semis  = sample.count(";")
    return "," if commas >= semis else ";"

def _parse_old_schema(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "parent_item": df["parent_item"].astype(str).str.strip(),
        "child_item":  df["child_item"].astype(str).str.strip(),
        "sequence_no": pd.to_numeric(df["sequence_no"], errors="coerce").fillna(0).astype(int),
        "level":       pd.to_numeric(df["level"], errors="coerce").fillna(0).astype(int),
    })
    out.sort_values(["parent_item","child_item","level","sequence_no"], inplace=True, kind="stable")
    out = out.drop_duplicates(subset=["parent_item","child_item","level"], keep="first").reset_index(drop=True)
    return out

def _parse_new_schema(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "parent_item": df["parent_item_id"].astype(str).str.strip(),
        "child_item":  df["child_item_id"].astype(str).str.strip(),
        "sequence_no": pd.to_numeric(df["sequenceno"], errors="coerce").fillna(0).astype(int),
        "level":       pd.to_numeric(df["bom_level"], errors="coerce").fillna(0).astype(int),
    })

    out.sort_values(["parent_item","child_item","level","sequence_no"], inplace=True, kind="stable")
    out = out.drop_duplicates(subset=["parent_item","child_item","level"], keep="first").reset_index(drop=True)
    return out

def parse_csv_text(
    text: str,
    filter_eng_ids: Optional[Iterable[str]] = None
) -> tuple[List[Dict], dict]:
    """
    Parse CSV text in either schema, optionally filtering the *new* schema by eng_id.
    Returns (rows, meta) where rows are canonical dicts and meta has details about filtering.
    """
    sample = text[:2048]
    sep = _sniff_delimiter(sample)
    try:
        df = pd.read_csv(io.StringIO(text), sep=sep, engine="c", dtype=str, keep_default_na=False)
    except Exception:
        df = pd.read_csv(io.StringIO(text), sep=None, engine="python", dtype=str, keep_default_na=False)

    df.columns = _normalize_cols(df.columns)
    cols = set(df.columns)

    meta = {
        "schema": None,           # "old" | "new"
        "filtered": False,
        "eng_ids": None,
        "rows_in": int(df.shape[0]),
        "rows_out": None,
    }

    if {"parent_item","child_item","sequence_no","level"}.issubset(cols):
        meta["schema"] = "old"
        out = _parse_old_schema(df)

    elif {"system_id","parent_item_id","child_item_id","bom_level","sequenceno","path"}.issubset(cols):
        meta["schema"] = "new"
        if filter_eng_ids:
            system_ids = sorted({str(x).strip() for x in filter_eng_ids if str(x).strip()})
            if not system_ids:
                raise HTTPException(status_code=400, detail="system_ids provided but empty after normalization")
            df = df[df["system_id"].isin(system_ids)].copy()
            meta["filtered"] = True
            meta["system_ids"] = system_ids
        out = _parse_new_schema(df)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"CSV headers not recognized. Expected either "
                   f"[parent_item, child_item, sequence_no, level] or "
                   f"[system_id, parent_item_id, child_item_id, bom_level, sequenceno, path]. Found: {list(df.columns)}"
        )

    meta["rows_out"] = int(out.shape[0])
    return out.to_dict(orient="records"), meta

def save_bytes_unique(name: str, raw: bytes) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).name) or "uploaded.csv"
    p = DATA_DIR / safe
    if not p.exists():
        p.write_bytes(raw)
    return p

def read_server_csv(
    filename: str,
    filter_eng_ids: Optional[Iterable[str]] = None
) -> Tuple[str, List[Dict], Path, dict]:
    """
    Reads CSV from data/, optionally filters by eng_id (new schema only).
    Returns (dataset_sha, rows, path, meta).

    The dataset SHA is made unique per (file, filter_eng_ids) so different scoped imports
    produce distinct datasets and won't dedupe against each other.
    """
    p = DATA_DIR / filename
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"CSV not found on server: {filename}")

    raw = p.read_bytes()
    text = raw.decode("utf-8", errors="replace")

    rows, meta = parse_csv_text(text, filter_eng_ids=filter_eng_ids)

    file_sha = sha256_bytes(raw)
    if meta["filtered"] and meta["eng_ids"]:
        scope_key = "eng_ids:" + ",".join(meta["eng_ids"])
        dataset_sha = sha256_text(file_sha + "|" + scope_key)
    else:
        dataset_sha = file_sha

    return dataset_sha, rows, p, meta
