# server/storage/sql_repository.py
from __future__ import annotations
from typing import Iterable, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import UploadFile, Relationship

class SqlGraphRepository:
    def __init__(self, session: AsyncSession):
        self._db = session

    async def list_datasets(self) -> list[dict]:
        res = await self._db.execute(select(UploadFile).order_by(UploadFile.created_at.desc()))
        out = []
        for ds in res.scalars():
            out.append({
                "dataset_id": ds.id,
                "original_name": ds.original_name,
                "saved_path": ds.saved_path,
                "sha256": ds.sha256,
                "rows_loaded": ds.rows_loaded,
                "created_at": str(ds.created_at) if ds.created_at else None
            })
        return out

    async def get_dataset_id_by_sha(self, sha256: str) -> Optional[int]:
        res = await self._db.execute(select(UploadFile.id).where(UploadFile.sha256 == sha256).limit(1))
        return res.scalar_one_or_none()

    async def insert_dataset(self, original_name: str, saved_path: str, sha256: str, rows: Iterable[dict]) -> int:
        # Explicitly set is_active=False for compatibility with older schemas that enforce NOT NULL
        ds = UploadFile(
            original_name=original_name,
            saved_path=saved_path,
            sha256=sha256,
            rows_loaded=0,
            is_active=False,  # <-- add this
        )
        self._db.add(ds)
        await self._db.flush()  # obtain ds.id

        rels = [
            Relationship(
                dataset_id=ds.id,
                parent_item=row["parent_item"],
                child_item=row["child_item"],
                sequence_no=row["sequence_no"],
                level=row["level"],
            )
            for row in rows
        ]
        self._db.add_all(rels)
        ds.rows_loaded = len(rels)

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
        return {"id": row.parent_item, "name": row.parent_item, "sequence_no": row.sequence_no, "level": row.level}
