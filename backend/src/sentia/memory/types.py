"""Memory data types."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Memory:
    id: str
    content: str
    source_event_id: str
    source_event_type: str
    emotion: str
    emotion_intensity: float
    mood: str
    needs_snapshot: dict
    embedding: list[float]
    formed_at: datetime
    salience: float           # 0-1, emotional weight at formation (harder to forget)
    strength: float           # 0-1, current memory strength (decays over time)
    last_recalled_at: Optional[datetime] = None
    recall_count: int = 0

    @property
    def is_forgotten(self) -> bool:
        return self.strength < 0.05

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "source_event_id": self.source_event_id,
            "source_event_type": self.source_event_type,
            "emotion": self.emotion,
            "emotion_intensity": self.emotion_intensity,
            "mood": self.mood,
            "needs_snapshot": self.needs_snapshot,
            "formed_at": self.formed_at.isoformat(),
            "salience": round(self.salience, 4),
            "strength": round(self.strength, 4),
            "last_recalled_at": self.last_recalled_at.isoformat() if self.last_recalled_at else None,
            "recall_count": self.recall_count,
        }
