# helpers to read and write registry
from __future__ import annotations
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from .models import DbConnection, AppState

ACTIVE_KEY = "active_source"  # value examples: "csv:filename.csv" or "db:3"

async def list_connections(db: AsyncSession) -> list[dict]:
    res = await db.execute(select(DbConnection).order_by(DbConnection.created_at.desc()))
    out = []
    for row in res.scalars():
        out.append({
            "id": row.id,
            "name": row.name,
            "url": row.url,
            "created_at": str(row.created_at) if row.created_at else None,
            "last_used_at": str(row.last_used_at) if row.last_used_at else None,
            "is_active": bool(row.is_active),
            "has_api_key": bool(row.api_key),
        })
    return out

async def register_connection(db: AsyncSession, name: str, url: str, api_key: Optional[str]) -> int:
    conn = DbConnection(name=name, url=url, api_key=api_key or None, is_active=False)
    db.add(conn)
    await db.commit()
    await db.refresh(conn)
    return conn.id

async def _set_state(db: AsyncSession, key: str, value: str) -> None:
    cur = await db.get(AppState, key)
    if cur:
        cur.value = value
    else:
        db.add(AppState(key=key, value=value))
    await db.commit()

async def get_active_source(db: AsyncSession) -> Optional[Tuple[str, str]]:
    """Returns ('csv', filename) or ('db', id_str) or None"""
    row = await db.get(AppState, ACTIVE_KEY)
    if not row:
        return None
    val = row.value
    if val.startswith("csv:"):
        return ("csv", val.split("csv:",1)[1])
    if val.startswith("db:"):
        return ("db", val.split("db:",1)[1])
    return None

async def set_active_csv(db: AsyncSession, filename: str) -> None:
    # deactivate any db connection flags
    await db.execute(update(DbConnection).values(is_active=False))
    await _set_state(db, ACTIVE_KEY, f"csv:{filename}")

async def set_active_db(db: AsyncSession, conn_id: int) -> None:
    await db.execute(update(DbConnection).values(is_active=False))
    await db.execute(update(DbConnection).where(DbConnection.id == conn_id).values(is_active=True))
    await _set_state(db, ACTIVE_KEY, f"db:{conn_id}")
