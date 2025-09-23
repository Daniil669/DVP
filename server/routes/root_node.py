from fastapi import APIRouter

router = APIRouter()

sample_data = [
    {"parent_item": "MAT000001", "child_item": "MAT000004", "sequence_no": 1, "level": 1},
    {"parent_item": "MAT000001", "child_item": "MAT000007", "sequence_no": 10, "level": 1},
    {"parent_item": "MAT000001", "child_item": "MAT000008", "sequence_no": 11, "level": 1},
    {"parent_item": "MAT000002", "child_item": "MAT000017", "sequence_no": 1, "level": 2},
    {"parent_item": "MAT000004", "child_item": "MAT000018", "sequence_no": 1, "level": 2},
]

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