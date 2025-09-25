from fastapi import APIRouter
from data.sample_data import sample_data

router = APIRouter()
@router.get("/root_node")
async def get_root_node():
    parents = set()
    children = set()
    
    for item in sample_data:
        parents.add(item["parent_item"])
        children.add(item["child_item"])
        
    roots = parents - children
    
    return {"message": "root boy",
            "root_node": list(roots),
            "count": len(roots)
            }