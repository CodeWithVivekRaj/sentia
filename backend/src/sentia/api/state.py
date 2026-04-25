"""State endpoints - read model snapshots."""
from fastapi import APIRouter, HTTPException, Query
from . import deps

router = APIRouter(prefix="/state", tags=["state"])


@router.get("")
async def get_state():
    if not deps.state_projection:
        raise HTTPException(503, "State projection not initialized")
    return deps.state_projection.snapshot()


@router.get("/events")
async def get_events(
    limit: int = Query(50, ge=1, le=1000),
    since: int = Query(0, ge=0),
):
    if not deps.event_store:
        raise HTTPException(503, "Event store not initialized")
    events = await deps.event_store.get_since(sequence=since, limit=limit)
    return {
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }


@router.post("/llm/toggle")
async def toggle_llm(enabled: bool):
    from ..events.types import Event, EventType
    event_type = EventType.LLM_ENABLED if enabled else EventType.LLM_DISABLED
    event = Event(type=event_type, payload={"enabled": enabled})
    persisted = await deps.event_bus.emit(event)
    return {"llm_enabled": enabled, "event_id": persisted.id}
