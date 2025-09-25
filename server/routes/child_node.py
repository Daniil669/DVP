
# server/routes/child_node.py
from __future__ import annotations
from fastapi import APIRouter, Query
from utils.loader import ensure_data_loaded
from utils.sample_data import get_sample_data

router = APIRouter()

@router.get("/child_node")
async def get_child_node(
    node_id: str = Query(..., description="Parent node whose children to fetch"),
    limit: int | None = Query(None, ge=1, description="Max number of children to return"),
):
    # Ensure memory is hydrated from the newest CSV if needed
    ensure_data_loaded()

    data = get_sample_data()

    # Does the node exist anywhere (as parent or child)?
    exists = any(d["parent_item"] == node_id or d["child_item"] == node_id for d in data)
    if not exists:
        return {"error": f"Node {node_id} not found", "children": [], "count_children": 0}

    # Find this node's parent (if any)
    parent = next(
        (
            {
                "id": d["parent_item"],
                "name": d["parent_item"],
                "sequence_no": d["sequence_no"],
                "level": d["level"],
            }
            for d in data
            if d["child_item"] == node_id
        ),
        None,
    )

    # Collect children ordered by sequence_no
    children = [
        {
            "id": d["child_item"],
            "name": d["child_item"],
            "sequence_no": d["sequence_no"],
            "level": d["level"],
        }
        for d in data
        if d["parent_item"] == node_id
    ]
    children.sort(key=lambda x: x["sequence_no"])

    if limit is not None:
        children = children[:limit]

    return {
        "search_id": node_id,
        "parent": parent,
        "children": children,
        "count_children": len(children),
    }

