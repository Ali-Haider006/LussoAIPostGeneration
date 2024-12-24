from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def test_endpoint():
    return {"message": "Server is running"}
