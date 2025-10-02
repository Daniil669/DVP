# server/routes/root_node.py
from __future__ import annotations
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from utils.upload_csv import upload_csv
from utils.loader import ensure_data_loaded
from utils.sample_data import get_sample_data
from registry.session import get_registry_session
from registry.api import get_active_source
from sqlalchemy.ext.asyncio import AsyncSession
from db.context import get_session
from storage.sql_repository import SqlGraphRepository

router = APIRouter()

def _compute_roots_mem(data: List[dict]) -> list[str]:
    parents = {r["parent_item"] for r in data}
    children = {r["child_item"] for r in data}
    return sorted(parents - children)

@router.post("/root_node")
async def post_root_node(
    file: Optional[UploadFile] = File(None),
    reg: AsyncSession = Depends(get_registry_session),
    db_sess = Depends(get_session),
):
    """If file is provided: upload & load CSV (becomes active CSV).
       Otherwise: serve from active source (CSV or DB).
    """
    if file is not None:
        _ = await upload_csv(file)  # validates + saves + loads into memory
        # mark CSV as active (by its canonical saved name)
        from utils.upload_csv import _safe_name  # ok to import
        fname = _safe_name(file.filename)
        from registry.api import set_active_csv
        await set_active_csv(reg, fname)
        data = get_sample_data()
        roots = _compute_roots_mem(data)
        return {"message": "Root node(s) computed (CSV)", "root_nodes": roots, "count": len(roots)}

    # no file: read from active source
    active = await get_active_source(reg)
    if not active or active[0] == "csv":
        ensure_data_loaded()
        data = get_sample_data()
        if not data:
            raise HTTPException(status_code=404, detail="No CSV data available.")
        roots = _compute_roots_mem(data)
        return {"message": "Root node(s) computed (CSV)", "root_nodes": roots, "count": len(roots)}

    # DB path
    repo = SqlGraphRepository(db_sess)
    roots = await repo.list_roots()
    if not roots:
        raise HTTPException(status_code=404, detail="No data in active DB dataset.")
    return {"message": "Root node(s) computed (DB)", "root_nodes": roots, "count": len(roots)}

@router.get("/root_node")
async def get_root_node(
    reg: AsyncSession = Depends(get_registry_session),
    db_sess = Depends(get_session),
):
    active = await get_active_source(reg)
    if not active or active[0] == "csv":
        ensure_data_loaded()
        data = get_sample_data()
        if not data:
            raise HTTPException(status_code=404, detail="No CSV data available.")
        roots = _compute_roots_mem(data)
        return {"message": "Root node(s) computed (CSV)", "root_nodes": roots, "count": len(roots)}
    repo = SqlGraphRepository(db_sess)
    roots = await repo.list_roots()
    if not roots:
        raise HTTPException(status_code=404, detail="No data in active DB dataset.")
    return {"message": "Root node(s) computed (DB)", "root_nodes": roots, "count": len(roots)}
