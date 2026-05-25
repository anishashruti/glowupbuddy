from fastapi import APIRouter
from config.database import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health():
    collections = get_db().list_collection_names()
    return {"status": "ok", "mongo": "connected", "collections": collections}
