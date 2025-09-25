from fastapi import APIRouter
from data.sample_data import current_data

router = APIRouter()
@router.get("/nodes/{node_id}/children")
async def get_node_children(node_id: str):
    children = []
    parent = []
    for relationship in current_data:
        if relationship["parent_item"] == node_id:
            child_info = {
                "id": relationship["child_item"],
                "name": relationship["child_item"],
                "sequence_no": relationship["sequence_no"],
                "level": relationship["level"],
            }
            children.append(child_info)
        if relationship["child_item"] == node_id:
            parent_info = {
                "id": relationship["parent_item"],
                "name": relationship["parent_item"],
                "sequence_no": relationship["sequence_no"],
                "level": relationship["level"],
            }
            parent.append(parent_info)
    
    children.sort(key=lambda x: x["sequence_no"])

    search_id_exists = any(
        rel["parent_item"] == node_id or rel["child_item"] == node_id 
        for rel in current_data
    )
    
    if not search_id_exists:
        return {
            "error": f"Node {node_id} not found in data",
            "children": [],
            "count": 0
        }
    
    return {
        "search_id": node_id,
        "parent": parent[0] if parent else None,
        "children": children,
        "count_children": len(children)
    }