from fastapi import APIRouter
from data.sample_data import current_data

router = APIRouter()
@router.get("/tree/full")
async def get_full_tree():
    all_items = set()
    for item in current_data:
        all_items.add(item["parent_item"])
        all_items.add(item["child_item"])
        
    tree_nodes=[]
    for item in all_items:
        children =[]
        for relationship in current_data:
            if relationship["parent_item"] == item:
                children.append({
                    "id": relationship["child_item"],
                    "name": relationship["child_item"],
                    "sequence_no": relationship["sequence_no"],
                    "level": relationship["level"]
                })
        children.sort(key=lambda x: x["sequence_no"])
        
        parent = None
        for relationship in sample_data:
            if relationship["child_item"] == item:
                parent = relationship["parent_item"]
                break
    
        node = {
            "id": item,
            "name": item,
            "parent": parent,
            "children": children,
            "children_count": len(children),
            "is_root": parent is None
        }
        tree_nodes.append(node)
    
    return {
        "message": "Full tree structure",
        "nodes": tree_nodes,
        "total_nodes": len(tree_nodes)
    }                     