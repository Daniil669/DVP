# server/storage/sql_repository.py
from __future__ import annotations
from typing import Iterable, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import UploadFile, Relationship

class SqlGraphRepository:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def get_active_dataset_id(self) -> Optional[int]:
        q = select(UploadFile.id).where(UploadFile.is_active.is_(True)).limit(1)
        r = await self._db.execute(q)
        return r.scalar_one_or_none()

    async def list_roots(self) -> list[str]:
        ds = await self.get_active_dataset_id()
        if ds is None:
            return []
        parents = select(Relationship.parent_item).where(Relationship.dataset_id == ds).subquery()
        children = select(Relationship.child_item).where(Relationship.dataset_id == ds).subquery()
        q = select(func.distinct(parents.c.parent_item)).where(
            ~parents.c.parent_item.in_(select(children.c.child_item))
        ).order_by(parents.c.parent_item.asc())
        r = await self._db.execute(q)
        return [row[0] for row in r.fetchall()]

    async def get_children(self, parent_id: str, limit: int | None = None) -> list[dict]:
        ds = await self.get_active_dataset_id()
        if ds is None:
            return []
        q = (
            select(Relationship.child_item, Relationship.sequence_no, Relationship.level)
            .where((Relationship.dataset_id == ds) & (Relationship.parent_item == parent_id))
            .order_by(Relationship.sequence_no.asc())
        )
        if limit:
            q = q.limit(limit)
        r = await self._db.execute(q)
        return [
            {"id": row.child_item, "name": row.child_item, "sequence_no": row.sequence_no, "level": row.level}
            for row in r.fetchall()
        ]

    async def get_parent(self, node_id: str) -> Optional[dict]:
        ds = await self.get_active_dataset_id()
        if ds is None:
            return None
        q = (
            select(Relationship.parent_item, Relationship.sequence_no, Relationship.level)
            .where((Relationship.dataset_id == ds) & (Relationship.child_item == node_id))
            .limit(1)
        )
        r = await self._db.execute(q)
        row = r.first()
        if not row:
            return None
        return {"id": row.parent_item, "name": row.parent_item, "sequence_no": row.sequence_no, "level": row.level}
