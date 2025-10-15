# server/routes/sources.py
from __future__ import annotations
from typing import Optional, Iterable, List
from fastapi import APIRouter, Depends, Body, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from registry.session import get_registry_session
from registry.api import list_connections, register_connection, get_connection
from registry.models import DbConnection
from db.engine_pool import get_engine
from storage.sql_repository import SqlGraphRepository
from utils.csv_import import DATA_DIR, read_server_csv

router = APIRouter()

@router.get("/sources")
async def get_sources(reg: AsyncSession = Depends(get_registry_session), connection_id: Optional[int] = None):
    csvs = []
    for p in sorted(DATA_DIR.glob("*.csv"), key=lambda x: x.stat().st_mtime, reverse=True):
        st = p.stat()
        csvs.append({"name": p.name, "size": st.st_size, "modified_at": int(st.st_mtime)})

    conns = await list_connections(reg)

    datasets = None
    if connection_id is not None:
        dbrow = await get_connection(reg, connection_id)
        if not dbrow:
            raise HTTPException(status_code=404, detail="connection not found")
        engine = get_engine(dbrow.url)
        Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        async with Session() as sess:
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
    payload: dict = Body(..., example={"connection_id": 1, "filename": "where_used.csv", "eng_ids": ["MODMAT000001","MODMAT000002"]}),
    api_key: Optional[str] = Header(default=None, alias="x-api-key"),
    reg: AsyncSession = Depends(get_registry_session),
):
    """
    Import a CSV from server data/ into a connection-scoped dataset.
    Optional scoping by one or more eng_id roots using 'eng_id' or 'eng_ids'.
    """
    conn_id = payload.get("connection_id")
    filename = payload.get("filename")
    one_eng  = payload.get("eng_id")
    many_eng = payload.get("eng_ids")

    if not conn_id or not filename:
        raise HTTPException(status_code=400, detail="connection_id and filename required")

    # Normalize eng_ids param
    filter_ids: Optional[List[str]] = None
    if one_eng and many_eng:
        raise HTTPException(status_code=400, detail="Provide either 'eng_id' or 'eng_ids', not both")
    if one_eng:
        filter_ids = [str(one_eng).strip()]
    elif isinstance(many_eng, list):
        filter_ids = [str(x).strip() for x in many_eng if str(x).strip()]

    # Fetch connection & check API key
    dbrow = await get_connection(reg, conn_id)
    if not dbrow:
        raise HTTPException(status_code=404, detail="connection not found")
    if dbrow.api_key and api_key != dbrow.api_key:
        raise HTTPException(status_code=401, detail="invalid API key")

    # Read & normalize rows (with optional eng_id filter)
    dataset_sha, rows, path, meta = read_server_csv(filename, filter_eng_ids=filter_ids)

    # Open a session and insert (dedupe by sha)
    engine = get_engine(dbrow.url)
    Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as sess:
        repo = SqlGraphRepository(sess)
        existing = await repo.get_dataset_id_by_sha(dataset_sha)
        if existing:
            return {
                "message": "dataset already exists",
                "dataset_id": existing,
                "sha256": dataset_sha,
                "rows": len(rows),
                "filtered": meta.get("filtered", False),
                "eng_ids": meta.get("eng_ids"),
            }
        ds_id = await repo.insert_dataset(
            original_name=filename,
            saved_path=str(path),
            sha256=dataset_sha,
            rows=rows
        )
        return {
            "message": "dataset imported",
            "dataset_id": ds_id,
            "sha256": dataset_sha,
            "rows": len(rows),
            "filtered": meta.get("filtered", False),
            "eng_ids": meta.get("eng_ids"),
        }
