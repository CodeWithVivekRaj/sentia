"""Shared FastAPI dependencies / app-level singletons."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..events.store import EventStore
    from ..events.bus import EventBus
    from ..events.projections import StateProjection
    from ..llm.model_manager import ModelManager
    from ..llm.ollama_adapter import OllamaAdapter
    from .websocket import ConnectionManager
    from ..memory.engine import MemoryEngine
    from ..mind.engine import MindEngine
    from ..social.whatsapp import WhatsAppNotifier
    from ..social.bonds import BondTracker
    from ..self.personality import PersonalityEngine
    from ..rewards.engine import RewardEngine

# These are set by main.py at startup
event_store: "EventStore | None" = None
event_bus: "EventBus | None" = None
state_projection: "StateProjection | None" = None
model_manager: "ModelManager | None" = None
llm_adapter: "OllamaAdapter | None" = None
ws_manager: "ConnectionManager | None" = None
memory_engine: "MemoryEngine | None" = None
mind_engine: "MindEngine | None" = None
whatsapp: "WhatsAppNotifier | None" = None
bond_tracker: "BondTracker | None" = None
personality_engine: "PersonalityEngine | None" = None
reward_engine: "RewardEngine | None" = None
