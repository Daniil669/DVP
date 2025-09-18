from fastapi import APIRouter

router = APIRouter()

@router.get("/root_node")
async def get_root_node():
    return {"message": "root boy"}