# server/routes/child_node.py
from __future__ import annotations
from fastapi import APIRouter, Query, Depends, HTTPException
from utils.loader import ensure_data_loaded
from utils.sample_data import get_sample_data
from registry.session import get_registry_session
from registry.api import get_active_source
from db.context import get_session
from storage.sql_repository import SqlGraphRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/child_node")
async def get_child_node(
    node_id: str = Query(..., description="Parent node whose children to fetch"),
    limit: int | None = Query(None, ge=1, description="Max number of children to return"),
    reg: AsyncSession = Depends(get_registry_session),
    db_sess = Depends(get_session),
):
    active = await get_active_source(reg)
    if not active or active[0] == "csv":
        ensure_data_loaded()
        data = get_sample_data()

        exists = any(d["parent_item"] == node_id or d["child_item"] == node_id for d in data)
        if not exists:
            return {"error": f"Node {node_id} not found", "children": [], "count_children": 0}

        parent = next(
            (
                {"id": d["parent_item"], "name": d["parent_item"], "sequence_no": d["sequence_no"], "level": d["level"]}
                for d in data if d["child_item"] == node_id
            ),
            None,
        )

        children = [
            {"id": d["child_item"], "name": d["child_item"], "sequence_no": d["sequence_no"], "level": d["level"]}
            for d in data if d["parent_item"] == node_id
        ]
        children.sort(key=lambda x: x["sequence_no"])
        if limit is not None:
            children = children[:limit]

        return {"search_id": node_id, "parent": parent, "children": children, "count_children": len(children)}

    # DB path
    repo = SqlGraphRepository(db_sess)
    parent = await repo.get_parent(node_id)
    children = await repo.get_children(node_id, limit=limit)
    if not parent and not children:
        return {"error": f"Node {node_id} not found", "children": [], "count_children": 0}
    return {"search_id": node_id, "parent": parent, "children": children, "count_children": len(children)}
