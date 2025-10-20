# server/storage/sql_repository.py
from __future__ import annotations
from typing import Iterable, Optional, List, Dict
from sqlalchemy import select, func, insert
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import UploadFile, Relationship

class SqlGraphRepository:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def list_datasets(self) -> list[dict]:
        res = await self._db.execute(select(UploadFile).order_by(UploadFile.created_at.desc()))
        return [
            {
                "dataset_id": ds.id,
                "original_name": ds.original_name,
                "saved_path": ds.saved_path,
                "sha256": ds.sha256,
                "rows_loaded": ds.rows_loaded,
                "created_at": str(ds.created_at) if ds.created_at else None,
            }
            for ds in res.scalars()
        ]

    async def get_dataset_id_by_sha(self, sha256: str) -> Optional[int]:
        res = await self._db.execute(select(UploadFile.id).where(UploadFile.sha256 == sha256).limit(1))
        return res.scalar_one_or_none()

    async def insert_dataset(self, original_name: str, saved_path: str, sha256: str, rows: List[Dict]) -> int:
        # Create dataset row
        ds = UploadFile(
            original_name=original_name,
            saved_path=saved_path,
            sha256=sha256,
            rows_loaded=0,
            is_active=False,  # keep old schemas happy
        )
        self._db.add(ds)
        await self._db.flush()  # get ds.id

        # Prepare relationship payload for executemany
        payload = [
            {
                "dataset_id": ds.id,
                "parent_item": r["parent_item"],
                "child_item":  r["child_item"],
                "sequence_no": r["sequence_no"],
                "level":       r["level"],
            }
            for r in rows
        ]

        if payload:
            stmt = insert(Relationship)
            await self._db.execute(stmt, payload)

        ds.rows_loaded = len(payload)
        await self._db.commit()
        return ds.id

    async def list_roots(self, dataset_id: int) -> list[str]:
        parents = select(Relationship.parent_item).where(Relationship.dataset_id == dataset_id).subquery()
        children = select(Relationship.child_item).where(Relationship.dataset_id == dataset_id).subquery()
        q = select(func.distinct(parents.c.parent_item)).where(
            ~parents.c.parent_item.in_(select(children.c.child_item))
        ).order_by(parents.c.parent_item.asc())
        res = await self._db.execute(q)
        return [r[0] for r in res.fetchall()]

    async def get_children(self, dataset_id: int, parent_id: str, limit: int | None = None) -> list[dict]:
        q = (
            select(Relationship.child_item, Relationship.sequence_no, Relationship.level)
            .where((Relationship.dataset_id == dataset_id) & (Relationship.parent_item == parent_id))
            .order_by(Relationship.sequence_no.asc())
        )
        if limit:
            q = q.limit(limit)
        res = await self._db.execute(q)
        return [
            {"id": row.child_item, "name": row.child_item, "sequence_no": row.sequence_no, "level": row.level}
            for row in res.fetchall()
        ]

    async def get_parent(self, dataset_id: int, node_id: str) -> Optional[dict]:
        q = (
            select(Relationship.parent_item, Relationship.sequence_no, Relationship.level)
            .where((Relationship.dataset_id == dataset_id) & (Relationship.child_item == node_id))
            .limit(1)
        )
        res = await self._db.execute(q)
        row = res.first()
        if not row:
            return None
        
        parent_id = row.parent_item
        q2 = (
            select(Relationship.sequence_no, Relationship.level)
            .where((Relationship.dataset_id == dataset_id) & (Relationship.child_item == parent_id))
            .limit(1)
        )
        res2 = await self._db.execute(q2)
        parent_data = res2.first()
        
        if parent_data:
            return {
                "id": parent_id,
                "name": parent_id,
                "sequence_no": parent_data.sequence_no,
                "level": parent_data.level
            }
        else:
            # If parent has no parent (it's a root), return with default values
            return{
                "id": parent_id,
                "name": parent_id,
                "sequence_no": 0,  # or whatever default you prefer for roots
                "level": 0
            }
