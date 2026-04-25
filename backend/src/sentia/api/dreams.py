"""Dreams API — browse Sentia's dream log."""
from fastapi import APIRouter, Query
from ..events.types import EventType
from . import deps

router = APIRouter(tags=["dreams"])


@router.get("/dreams")
async def list_dreams(limit: int = Query(20, ge=1, le=100)):
    store = deps.event_store
    if not store:
        return []

    events = await store.get_by_type(EventType.DREAM_OCCURRED, limit)
    result = []
    for e in events:
        payload = e.payload
        result.append({
            "id": e.id,
            "content": payload.get("content", ""),
            "emotion": payload.get("emotion", ""),
            "memory_count": payload.get("memory_count", 0),
            "timestamp": e.timestamp.isoformat(),
        })
    return result
