from fastapi import APIRouter, Query
from . import deps
from ..events.types import EventType

router = APIRouter(prefix="/chronicle", tags=["chronicle"])

# Event types that constitute life milestones
MILESTONE_TYPES = [
    EventType.AI_BORN,
    EventType.LIFE_STAGE_CHANGED,
    EventType.EMOTION_EMERGED,
    EventType.INSIGHT_FORMED,
    EventType.DREAM_OCCURRED,
    EventType.MEMORY_CONSOLIDATED,
    EventType.BOND_FORMED,
    EventType.NEED_CRITICAL,
    EventType.MODEL_CHANGED,
    EventType.MOOD_SHIFTED,
]


@router.get("")
async def get_chronicle(limit: int = Query(100, ge=1, le=500)):
    store = deps.event_store
    if not store:
        return {"milestones": []}

    # Fetch each milestone type and merge
    all_events = []
    for et in MILESTONE_TYPES:
        events = await store.get_by_type(et, limit=50)
        all_events.extend(events)

    # Sort by sequence, deduplicate, take most recent `limit`
    all_events.sort(key=lambda e: e.sequence)
    # Keep only last `limit`
    all_events = all_events[-limit:]

    # Format as milestone entries
    milestones = []
    seen_emotions: set[str] = set()  # Only include first occurrence of each emotion
    for event in all_events:
        if event.type == EventType.EMOTION_EMERGED:
            emotion = event.payload.get("emotion", "")
            if emotion in seen_emotions:
                continue
            seen_emotions.add(emotion)

        milestones.append({
            "id": event.id,
            "type": event.type.value,
            "payload": event.payload,
            "timestamp": event.timestamp.isoformat(),
            "sequence": event.sequence,
            "label": _milestone_label(event),
        })

    return {"milestones": milestones}


def _milestone_label(event) -> str:
    p = event.payload
    if event.type == EventType.AI_BORN:
        return "Sentia was born"
    if event.type == EventType.LIFE_STAGE_CHANGED:
        return f"Entered {p.get('stage', 'new')} stage"
    if event.type == EventType.EMOTION_EMERGED:
        return f"First felt {p.get('emotion', 'something')}"
    if event.type == EventType.INSIGHT_FORMED:
        content = p.get("content", "")
        return f"Insight: {content[:60]}{'…' if len(content) > 60 else ''}"
    if event.type == EventType.DREAM_OCCURRED:
        return f"Dreamed ({p.get('memory_count', 0)} memories woven)"
    if event.type == EventType.NEED_CRITICAL:
        return f"Need critical: {p.get('need', 'unknown')}"
    if event.type == EventType.MODEL_CHANGED:
        return f"Model changed to {p.get('model', 'unknown')}"
    if event.type == EventType.MOOD_SHIFTED:
        return f"Mood shifted to {p.get('mood', 'unknown')}"
    if event.type == EventType.BOND_FORMED:
        return "Bond formed"
    return event.type.value
