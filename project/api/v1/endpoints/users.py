from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_all_users():
    return [{"id": 1, "name": "Test User V1"}]
