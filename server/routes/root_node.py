
# server/routes/root_node.py
from __future__ import annotations
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException
from utils.upload_csv import upload_csv
from utils.loader import ensure_data_loaded
from utils.sample_data import get_sample_data

router = APIRouter()

def _compute_roots(data: List[dict]) -> list[str]:
    parents = {r["parent_item"] for r in data}
    children = {r["child_item"] for r in data}
    return sorted(parents - children)

@router.post("/root_node")
async def post_root_node(file: Optional[UploadFile] = File(None)):
    """
    If a file is provided: validate, save (if new), and load it.
    If not: ensure data is loaded from the latest CSV in /data.
    Then return root node(s).
    """
    if file is not None:
        _ = await upload_csv(file)  # validates + loads
    else:
        ensure_data_loaded()        # load newest if needed

    data = get_sample_data()
    if not data:
        raise HTTPException(status_code=400, detail="No relationships loaded.")

    roots = _compute_roots(data)
    return {
        "message": "Root node(s) computed",
        "root_nodes": roots,
        "count": len(roots),
    }

@router.get("/root_node")
async def get_root_node():
    """
    Read-only root computation (no upload). Ensures data is loaded from /data if needed.
    """
    ensure_data_loaded()
    data = get_sample_data()
    if not data:
        raise HTTPException(status_code=404, detail="No data available.")
    roots = _compute_roots(data)
    return {
        "message": "Root node(s) computed",
        "root_nodes": roots,
        "count": len(roots),
    }

