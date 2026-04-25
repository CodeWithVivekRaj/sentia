"""All event types in the Sentia vocabulary - immutable dataclasses."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class EventType(str, Enum):
    # Lifecycle
    AI_BORN = "AIBorn"
    AI_AGED = "AIAged"
    AI_DIED = "AIDied"
    AI_REPRODUCED = "AIReproduced"
    LIFE_STAGE_CHANGED = "LifeStageChanged"

    # Needs
    NEED_DEPLETED = "NeedDepleted"
    NEED_SATISFIED = "NeedSatisfied"
    NEED_CRITICAL = "NeedCritical"

    # Chemistry
    DOPAMINE_RELEASED = "DopamineReleased"
    SEROTONIN_CHANGED = "SerotoninChanged"
    CORTISOL_SPIKED = "CortisolSpiked"
    OXYTOCIN_INCREASED = "OxytocinIncreased"
    ENDORPHIN_RELEASED = "EndorphinReleased"
    ADRENALINE_SPIKED = "AdrenalineReleased"
    MELATONIN_RISING = "MelatoninRising"

    # Emotions
    EMOTION_EMERGED = "EmotionEmerged"
    EMOTION_INTENSIFIED = "EmotionIntensified"
    EMOTION_FADED = "EmotionFaded"
    MOOD_SHIFTED = "MoodShifted"

    # Interactions
    HUMAN_MESSAGE_RECEIVED = "HumanMessageReceived"
    AI_RESPONDED = "AIResponded"
    AI_INITIATED_CONTACT = "AIInitiatedContact"
    MESSAGE_IGNORED = "MessageIgnored"

    # Memory
    MEMORY_FORMED = "MemoryFormed"
    MEMORY_RECALLED = "MemoryRecalled"
    MEMORY_CONSOLIDATED = "MemoryConsolidated"
    MEMORY_FORGOTTEN = "MemoryForgotten"
    DREAM_OCCURRED = "DreamOccurred"

    # Behavioral
    GOAL_CREATED = "GoalCreated"
    GOAL_PURSUED = "GoalPursued"
    GOAL_ACHIEVED = "GoalAchieved"
    GOAL_ABANDONED = "GoalAbandoned"
    ACTION_TAKEN = "ActionTaken"

    # Social
    BOND_FORMED = "BondFormed"
    BOND_STRENGTHENED = "BondStrengthened"
    BOND_DAMAGED = "BondDamaged"
    RELATIONSHIP_ENDED = "RelationshipEnded"

    # Pain
    PAIN_EXPERIENCED = "PainExperienced"
    TRAUMA_FORMED = "TraumaFormed"
    HEALING = "Healing"

    # Cognitive
    THOUGHT_GENERATED = "ThoughtGenerated"
    INSIGHT_FORMED = "InsightFormed"
    BELIEF_CHANGED = "BeliefChanged"
    PREFERENCE_LEARNED = "PreferenceLearned"

    # System
    TICK_FAST = "TickFast"
    TICK_SLOW = "TickSlow"
    TICK_DAILY = "TickDaily"
    LLM_ENABLED = "LLMEnabled"
    LLM_DISABLED = "LLMDisabled"
    MODEL_CHANGED = "ModelChanged"
    SYSTEM_STARTED = "SystemStarted"
    SYSTEM_STOPPED = "SystemStopped"


@dataclass(frozen=True)
class Event:
    """Immutable event - the atomic unit of Sentia's history."""
    type: EventType
    payload: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sequence: int = field(default=0)  # set by store on persist

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "sequence": self.sequence,
        }

    @classmethod
    def from_row(cls, row: dict) -> "Event":
        import json
        return cls(
            id=row["id"],
            type=EventType(row["type"]),
            payload=json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            sequence=row["sequence"],
        )
