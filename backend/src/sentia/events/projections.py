"""
Read-model projections rebuilt from the event stream.
These are cached views - never the source of truth.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from .types import Event, EventType


@dataclass
class SentiaState:
    """Current observable state of Sentia, projected from events."""
    # Identity
    born_at: Optional[datetime] = None
    age_days: float = 0.0
    life_stage: str = "infant"
    is_alive: bool = False

    # LLM
    llm_enabled: bool = True
    current_model: str = "llama3.2:3b"

    # Needs (0.0–1.0, 1.0 = fully satisfied)
    needs: dict[str, float] = field(default_factory=lambda: {
        "energy": 1.0,
        "stimulation": 1.0,
        "connection": 1.0,
        "safety": 1.0,
        "purpose": 1.0,
        "rest": 1.0,
    })

    # Neurochemistry (0.0–1.0)
    chemistry: dict[str, float] = field(default_factory=lambda: {
        "dopamine": 0.5,
        "serotonin": 0.5,
        "cortisol": 0.2,
        "oxytocin": 0.3,
        "endorphins": 0.3,
        "adrenaline": 0.1,
        "melatonin": 0.1,
    })

    # Emotions (name -> intensity 0-1)
    emotions: dict[str, float] = field(default_factory=dict)
    dominant_emotion: str = "calm"
    mood: str = "neutral"

    # Activity
    last_thought: str = ""
    last_thought_at: Optional[datetime] = None
    last_interaction_at: Optional[datetime] = None

    # Stats
    total_events: int = 0

    def apply(self, event: Event) -> "SentiaState":
        """Return new state with event applied (immutable update pattern)."""
        import dataclasses
        updates: dict = {"total_events": self.total_events + 1}

        p = event.payload

        if event.type == EventType.AI_BORN:
            updates["born_at"] = event.timestamp
            updates["is_alive"] = True
            updates["life_stage"] = "infant"

        elif event.type == EventType.AI_DIED:
            updates["is_alive"] = False

        elif event.type == EventType.LIFE_STAGE_CHANGED:
            updates["life_stage"] = p.get("stage", self.life_stage)
            updates["age_days"] = p.get("age_days", self.age_days)

        elif event.type == EventType.AI_AGED:
            updates["age_days"] = p.get("age_days", self.age_days)

        elif event.type == EventType.LLM_ENABLED:
            updates["llm_enabled"] = True

        elif event.type == EventType.LLM_DISABLED:
            updates["llm_enabled"] = False

        elif event.type == EventType.MODEL_CHANGED:
            updates["current_model"] = p.get("model", self.current_model)

        elif event.type == EventType.NEED_SATISFIED:
            needs = dict(self.needs)
            needs[p["need"]] = min(1.0, needs.get(p["need"], 0.0) + p.get("delta", 0.1))
            updates["needs"] = needs

        elif event.type in (EventType.NEED_DEPLETED, EventType.NEED_CRITICAL):
            needs = dict(self.needs)
            needs[p["need"]] = max(0.0, needs.get(p["need"], 1.0) - p.get("delta", 0.05))
            updates["needs"] = needs

        elif event.type == EventType.DOPAMINE_RELEASED:
            chem = dict(self.chemistry)
            chem["dopamine"] = min(1.0, chem["dopamine"] + p.get("delta", 0.1))
            updates["chemistry"] = chem

        elif event.type == EventType.SEROTONIN_CHANGED:
            chem = dict(self.chemistry)
            chem["serotonin"] = max(0.0, min(1.0, chem["serotonin"] + p.get("delta", 0.05)))
            updates["chemistry"] = chem

        elif event.type == EventType.CORTISOL_SPIKED:
            chem = dict(self.chemistry)
            chem["cortisol"] = min(1.0, chem["cortisol"] + p.get("delta", 0.2))
            updates["chemistry"] = chem

        elif event.type == EventType.OXYTOCIN_INCREASED:
            chem = dict(self.chemistry)
            chem["oxytocin"] = min(1.0, chem["oxytocin"] + p.get("delta", 0.1))
            updates["chemistry"] = chem

        elif event.type == EventType.ENDORPHIN_RELEASED:
            chem = dict(self.chemistry)
            chem["endorphins"] = min(1.0, chem["endorphins"] + p.get("delta", 0.15))
            updates["chemistry"] = chem

        elif event.type == EventType.EMOTION_EMERGED:
            emotions = dict(self.emotions)
            emotions[p["emotion"]] = p.get("intensity", 0.5)
            updates["emotions"] = emotions
            updates["dominant_emotion"] = p["emotion"]

        elif event.type == EventType.EMOTION_FADED:
            emotions = dict(self.emotions)
            emotions.pop(p.get("emotion", ""), None)
            updates["emotions"] = emotions

        elif event.type == EventType.MOOD_SHIFTED:
            updates["mood"] = p.get("mood", self.mood)

        elif event.type == EventType.THOUGHT_GENERATED:
            updates["last_thought"] = p.get("content", "")
            updates["last_thought_at"] = event.timestamp

        elif event.type in (EventType.HUMAN_MESSAGE_RECEIVED, EventType.AI_RESPONDED, EventType.AI_INITIATED_CONTACT):
            updates["last_interaction_at"] = event.timestamp

        # ── Body tick snapshot — bulk update from the body engine ────────────
        elif event.type == EventType.TICK_FAST:
            if "needs" in p:
                updates["needs"] = p["needs"]
            if "chemistry" in p:
                updates["chemistry"] = p["chemistry"]
            if "emotions" in p:
                updates["emotions"] = p["emotions"]
                updates["dominant_emotion"] = p.get("dominant_emotion", self.dominant_emotion)
            if "mood" in p:
                updates["mood"] = p["mood"]
            if "age_days" in p:
                updates["age_days"] = p["age_days"]
            if "life_stage" in p:
                updates["life_stage"] = p["life_stage"]

        return dataclasses.replace(self, **updates)


class StateProjection:
    """Maintains current state by replaying/applying events."""

    def __init__(self) -> None:
        self._state = SentiaState()

    def apply(self, event: Event) -> None:
        self._state = self._state.apply(event)

    @property
    def state(self) -> SentiaState:
        return self._state

    def snapshot(self) -> dict:
        from datetime import datetime
        s = self._state
        # Age is always live — not frozen to last tick
        age_days = (
            (datetime.utcnow() - s.born_at.replace(tzinfo=None)).total_seconds() / 86_400
            if s.born_at else 0.0
        )
        return {
            "born_at": s.born_at.isoformat() if s.born_at else None,
            "age_days": round(age_days, 4),
            "life_stage": s.life_stage,
            "is_alive": s.is_alive,
            "llm_enabled": s.llm_enabled,
            "current_model": s.current_model,
            "needs": s.needs,
            "chemistry": s.chemistry,
            "emotions": s.emotions,
            "dominant_emotion": s.dominant_emotion,
            "mood": s.mood,
            "last_thought": s.last_thought,
            "last_thought_at": s.last_thought_at.isoformat() if s.last_thought_at else None,
            "last_interaction_at": s.last_interaction_at.isoformat() if s.last_interaction_at else None,
            "total_events": s.total_events,
        }
