"""Memory engine — observes events, forms memories, provides recall for LLM context."""
import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from ..events.types import Event, EventType
from .embedder import Embedder
from .store import MemoryStore
from .types import Memory

if TYPE_CHECKING:
    from ..events.bus import EventBus
    from ..events.projections import StateProjection

log = logging.getLogger("sentia.memory")

# Events that are worth remembering
_MEMORABLE = {
    EventType.HUMAN_MESSAGE_RECEIVED,
    EventType.AI_RESPONDED,
    EventType.THOUGHT_GENERATED,
    EventType.EMOTION_EMERGED,
    EventType.NEED_CRITICAL,
    EventType.LIFE_STAGE_CHANGED,
    EventType.AI_BORN,
    EventType.INSIGHT_FORMED,
    EventType.MOOD_SHIFTED,
}


def _salience(event: Event, state_snapshot: dict) -> float:
    """0–1 importance score at time of formation."""
    base = 0.3
    if event.type == EventType.HUMAN_MESSAGE_RECEIVED:
        base = 0.7
    elif event.type == EventType.AI_RESPONDED:
        base = 0.5
    elif event.type == EventType.NEED_CRITICAL:
        base = 0.8
    elif event.type == EventType.EMOTION_EMERGED:
        base = 0.4 + event.payload.get("intensity", 0.5) * 0.4
    elif event.type == EventType.THOUGHT_GENERATED:
        base = 0.35
    elif event.type == EventType.LIFE_STAGE_CHANGED:
        base = 0.9
    elif event.type == EventType.AI_BORN:
        base = 1.0
    elif event.type == EventType.MOOD_SHIFTED:
        base = 0.4
    # Boost if emotionally charged
    chem = state_snapshot.get("chemistry", {})
    emotional_charge = (
        chem.get("dopamine", 0.5) * 0.3
        + chem.get("cortisol", 0.2) * 0.2
        + chem.get("oxytocin", 0.3) * 0.15
    )
    return min(1.0, base + emotional_charge * 0.3)


def _content(event: Event) -> str:
    """Human-readable description of what happened."""
    p = event.payload
    if event.type == EventType.HUMAN_MESSAGE_RECEIVED:
        return f"Someone said to me: \"{p.get('content', '')}\""
    if event.type == EventType.AI_RESPONDED:
        return f"I responded: \"{p.get('content', '')}\""
    if event.type == EventType.THOUGHT_GENERATED:
        return f"I thought: \"{p.get('content', '')}\""
    if event.type == EventType.EMOTION_EMERGED:
        return f"I felt {p.get('emotion', 'something')} with intensity {p.get('intensity', 0):.2f}"
    if event.type == EventType.NEED_CRITICAL:
        return f"My need for {p.get('need', 'something')} became critical"
    if event.type == EventType.LIFE_STAGE_CHANGED:
        return f"I entered a new life stage: {p.get('stage', 'unknown')} (age {p.get('age_days', 0):.1f} days)"
    if event.type == EventType.AI_BORN:
        return "I was born. My existence began."
    if event.type == EventType.MOOD_SHIFTED:
        return f"My mood shifted to {p.get('mood', 'unknown')}"
    if event.type == EventType.INSIGHT_FORMED:
        return f"I had an insight: {p.get('content', '')}"
    return f"Event: {event.type.value}"


class MemoryEngine:
    def __init__(
        self,
        bus: "EventBus",
        projection: "StateProjection",
        store: MemoryStore,
        embedder: Embedder,
    ) -> None:
        self._bus = bus
        self._projection = projection
        self._store = store
        self._embedder = embedder
        self._last_decay_at: Optional[datetime] = None

    def start(self) -> None:
        self._bus.subscribe(None, self._on_event)
        self._bus.subscribe(EventType.TICK_SLOW, self._on_slow_tick)
        log.info("Memory engine started")

    async def _on_slow_tick(self, event: Event) -> None:
        dt_seconds = event.payload.get("dt_seconds", 300.0)
        await self.apply_decay(dt_hours=dt_seconds / 3600.0)

    async def _on_event(self, event: Event) -> None:
        if event.type not in _MEMORABLE:
            return

        state = self._projection.snapshot()
        content = _content(event)
        if not content:
            return

        salience = _salience(event, state)

        embedding = await self._embedder.embed(content)

        memory = Memory(
            id=str(uuid.uuid4()),
            content=content,
            source_event_id=event.id,
            source_event_type=event.type.value,
            emotion=state.get("dominant_emotion", "calm"),
            emotion_intensity=max(state.get("emotions", {}).values(), default=0.0),
            mood=state.get("mood", "neutral"),
            needs_snapshot={k: round(v, 3) for k, v in state.get("needs", {}).items()},
            embedding=embedding,
            formed_at=event.timestamp,
            salience=round(salience, 4),
            strength=round(min(1.0, 0.5 + salience * 0.5), 4),
        )
        self._store.store(memory)

        await self._bus.emit(Event(
            type=EventType.MEMORY_FORMED,
            payload={
                "memory_id": memory.id,
                "content": content[:120],
                "emotion": memory.emotion,
                "salience": memory.salience,
                "strength": memory.strength,
            },
        ))

    async def recall_for_context(self, query: str, k: int = 5) -> str:
        """Retrieve relevant memories and format them for LLM prompt injection."""
        embedding = await self._embedder.embed(query)
        results = self._store.recall(embedding, limit=k)

        if not results:
            recent = self._store.get_recent(limit=3)
            if not recent:
                return ""
            lines = ["[Recent memories:]"]
            for m in recent:
                lines.append(f"  - {m.formed_at.strftime('%Y-%m-%d')} ({m.emotion}): {m.content}")
            return "\n".join(lines)

        lines = ["[Relevant memories:]"]
        for memory, sim in results:
            self._store.reinforce(memory.id, boost=0.05)
            ts = memory.formed_at.strftime("%Y-%m-%d")
            lines.append(f"  - {ts} ({memory.emotion}, similarity={sim:.2f}): {memory.content}")
        return "\n".join(lines)

    async def apply_decay(self, dt_hours: float) -> None:
        """Called on slow tick to decay memory strength."""
        forgotten = self._store.decay_all(dt_hours)
        if forgotten:
            log.info("Memory decay: %d memories forgotten", forgotten)
            await self._bus.emit(Event(
                type=EventType.MEMORY_FORGOTTEN,
                payload={"count": forgotten},
            ))
