# server/routes/sources.py
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, Body, HTTPException, Header
from utils.loader import list_csv_files, load_csv_file, DATA_DIR
from registry.session import get_registry_session
from registry.api import list_connections, register_connection, set_active_csv, set_active_db, get_active_source
from registry.models import DbConnection  # <-- import the real model
from db.context import set_current_db_url
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from pathlib import Path

router = APIRouter()

@router.get("/sources")
async def get_sources(reg: AsyncSession = Depends(get_registry_session)):
    csvs = list_csv_files()
    conns = await list_connections(reg)
    active = await get_active_source(reg)
    return {
        "csv_files": csvs,
        "db_connections": conns,
        "active": {"type": active[0], "value": active[1]} if active else None
    }

@router.post("/sources/select")
async def select_source(
    payload: dict = Body(..., example={"type": "csv", "filename": "where_used.csv"}),
    api_key: Optional[str] = Header(default=None, alias="x-api-key"),
    reg: AsyncSession = Depends(get_registry_session),
):
    stype = payload.get("type")
    if stype == "csv":
        fname = payload.get("filename")
        if not fname:
            raise HTTPException(status_code=400, detail="filename required")
        p = DATA_DIR / fname
        n = load_csv_file(p)  # loads into in-memory store
        await set_active_csv(reg, fname)
        set_current_db_url(None)  # switch graph context back to default local URL
        return {"message": "active source set to CSV", "filename": fname, "rows_loaded": n}

    elif stype == "db":
        conn_id = payload.get("connection_id")
        if not conn_id:
            raise HTTPException(status_code=400, detail="connection_id required")

        # fetch the stored connection by ID
        found = await reg.get(DbConnection, conn_id)
        if not found:
            raise HTTPException(status_code=404, detail="connection not found")

        # simple header-based check (optional)
        if found.api_key and api_key != found.api_key:
            raise HTTPException(status_code=401, detail="invalid API key")

        # activate this connection and mark last_used_at
        await set_active_db(reg, conn_id)
        await reg.execute(
            update(DbConnection)
            .where(DbConnection.id == conn_id)
            .values(last_used_at=None)  # let DB default set if you prefer server time; or set to func.now()
        )
        await reg.commit()

        # point the graph DB context at this URL
        set_current_db_url(found.url)

        return {"message": "active source set to DB", "connection_id": conn_id, "url": found.url}

    else:
        raise HTTPException(status_code=400, detail="type must be 'csv' or 'db'")

@router.post("/db/register")
async def register_db(
    name: str = Body(...),
    url: str = Body(..., example="sqlite+aiosqlite:///./data/app.db"),
    api_key: Optional[str] = Body(None),
    reg: AsyncSession = Depends(get_registry_session),
):
    cid = await register_connection(reg, name=name, url=url, api_key=api_key)
    return {"message": "db connection registered", "connection_id": cid}
