from fastapi import APIRouter

router = APIRouter()

@router.get("/child_node")
async def get_child_node():
    return {"message": "child"}