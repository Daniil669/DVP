# server/routes/sources.py
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, Body, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from registry.session import get_registry_session
from registry.api import list_connections, register_connection, get_connection
from registry.models import DbConnection
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from db.engine_pool import get_engine
from storage.sql_repository import SqlGraphRepository
from utils.csv_import import DATA_DIR, read_server_csv

router = APIRouter()

@router.get("/sources")
async def get_sources(reg: AsyncSession = Depends(get_registry_session), connection_id: Optional[int] = None):
    """
    Lists:
      - CSV files present on server (data/)
      - Known DB connections in registry
      - If connection_id is provided, also list datasets in that DB
    """
    # CSVs on disk
    csvs = []
    for p in sorted(DATA_DIR.glob("*.csv"), key=lambda x: x.stat().st_mtime, reverse=True):
        st = p.stat()
        csvs.append({"name": p.name, "size": st.st_size, "modified_at": int(st.st_mtime)})

    # DB connections
    conns = await list_connections(reg)

    datasets = None
    if connection_id is not None:
        dbrow = await get_connection(reg, connection_id)
        if not dbrow:
            raise HTTPException(status_code=404, detail="connection not found")
        # open a session on that URL and list datasets
        engine = get_engine(dbrow.url)
        Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        async with Session() as sess:
            # ensure tables exist (idempotent) — optional safety
            await sess.execute(text("SELECT 1"))
            repo = SqlGraphRepository(sess)
            datasets = await repo.list_datasets()

    return {"csv_files": csvs, "db_connections": conns, "datasets": datasets}

@router.post("/db/register")
async def register_db(
    name: str = Body(...),
    url: str = Body(..., example="sqlite+aiosqlite:///./data/app.db"),
    api_key: Optional[str] = Body(None),
    reg: AsyncSession = Depends(get_registry_session),
):
    cid = await register_connection(reg, name=name, url=url, api_key=api_key)
    return {"message": "db connection registered", "connection_id": cid}

@router.post("/sources/import_csv")
async def import_csv_to_db(
    payload: dict = Body(..., example={"connection_id": 1, "filename": "where_used.csv"}),
    api_key: Optional[str] = Header(default=None, alias="x-api-key"),
    reg: AsyncSession = Depends(get_registry_session),
):
    """
    Import an existing server CSV (data/filename) into the selected DB connection as a dataset.
    Deduped by SHA-256; returns existing dataset_id if already imported.
    """
    conn_id = payload.get("connection_id")
    filename = payload.get("filename")
    if not conn_id or not filename:
        raise HTTPException(status_code=400, detail="connection_id and filename required")

    # fetch connection & check simple header-based key
    dbrow = await get_connection(reg, conn_id)
    if not dbrow:
        raise HTTPException(status_code=404, detail="connection not found")
    if dbrow.api_key and api_key != dbrow.api_key:
        raise HTTPException(status_code=401, detail="invalid API key")

    sha, rows, path = read_server_csv(filename)

    # open a session for this connection URL
    engine = get_engine(dbrow.url)
    Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as sess:
        repo = SqlGraphRepository(sess)
        existing = await repo.get_dataset_id_by_sha(sha)
        if existing:
            return {"message": "dataset already exists", "dataset_id": existing, "sha256": sha, "rows": len(rows)}
        ds_id = await repo.insert_dataset(original_name=filename, saved_path=str(path), sha256=sha, rows=rows)
        return {"message": "dataset imported", "dataset_id": ds_id, "sha256": sha, "rows": len(rows)}
