"""Personality trait tracking — 6 traits that evolve from lived experience."""
import hashlib
import logging
import sqlite3
from typing import TYPE_CHECKING

from ..events.types import EventType

if TYPE_CHECKING:
    from ..events.bus import EventBus

log = logging.getLogger("sentia.personality")

TRAIT_NAMES = ["curiosity", "warmth", "resilience", "creativity", "introversion", "openness"]


class PersonalityEngine:
    """Manages Sentia's 6 personality traits that evolve from lived experience."""

    def __init__(self) -> None:
        self._con: sqlite3.Connection | None = None
        self._traits: dict[str, float] = {}

    def initialize(self, db_path: str, genome_seed: str = "default") -> None:
        """Create traits table and seed from genome if empty."""
        self._con = sqlite3.connect(db_path, check_same_thread=False)
        self._con.execute(
            "CREATE TABLE IF NOT EXISTS traits (id TEXT PRIMARY KEY, value REAL)"
        )
        self._con.commit()

        # Check if table is empty
        row = self._con.execute("SELECT COUNT(*) FROM traits").fetchone()
        if row[0] == 0:
            self._seed_from_genome(genome_seed)
        else:
            self._load()

        log.info("PersonalityEngine initialized. Traits: %s", self._traits)

    def _seed_from_genome(self, seed: str) -> None:
        """Derive initial trait values deterministically from genome seed."""
        h = hashlib.sha256(seed.encode()).digest()
        for i, trait in enumerate(TRAIT_NAMES):
            value = round(0.3 + (h[i] / 255) * 0.4, 3)
            self._traits[trait] = value
            self._con.execute(
                "INSERT OR REPLACE INTO traits (id, value) VALUES (?, ?)",
                (trait, value),
            )
        self._con.commit()
        log.info("Personality seeded from genome '%s': %s", seed, self._traits)

    def _load(self) -> None:
        """Load trait values from SQLite."""
        rows = self._con.execute("SELECT id, value FROM traits").fetchall()
        self._traits = {row[0]: row[1] for row in rows}

    def start(self, bus: "EventBus") -> None:
        """Subscribe to events that shape personality over time."""
        bus.subscribe(EventType.THOUGHT_GENERATED, self._on_thought_generated)
        bus.subscribe(EventType.INSIGHT_FORMED, self._on_insight_formed)
        bus.subscribe(EventType.HUMAN_MESSAGE_RECEIVED, self._on_human_message_received)
        bus.subscribe(EventType.OXYTOCIN_INCREASED, self._on_oxytocin_increased)
        bus.subscribe(EventType.NEED_CRITICAL, self._on_need_critical)
        bus.subscribe(EventType.DREAM_OCCURRED, self._on_dream_occurred)
        bus.subscribe(EventType.BELIEF_CHANGED, self._on_belief_changed)
        log.info("PersonalityEngine started and subscribed to events")

    async def _on_thought_generated(self, event) -> None:
        self._update("curiosity", +0.002)
        self._update("creativity", +0.001)
        self._update("introversion", +0.001)

    async def _on_insight_formed(self, event) -> None:
        self._update("curiosity", +0.003)
        self._update("openness", +0.003)
        self._update("creativity", +0.002)

    async def _on_human_message_received(self, event) -> None:
        self._update("warmth", +0.002)
        self._update("introversion", -0.001)

    async def _on_oxytocin_increased(self, event) -> None:
        self._update("warmth", +0.001)

    async def _on_need_critical(self, event) -> None:
        self._update("resilience", -0.001)

    async def _on_dream_occurred(self, event) -> None:
        self._update("creativity", +0.003)

    async def _on_belief_changed(self, event) -> None:
        self._update("openness", +0.002)

    def _update(self, trait: str, delta: float) -> None:
        """Apply delta to a trait, clamp to [0.1, 0.9], and persist."""
        if trait not in self._traits:
            log.warning("Unknown trait: %s", trait)
            return
        new_value = round(max(0.1, min(0.9, self._traits[trait] + delta)), 4)
        self._traits[trait] = new_value
        if self._con:
            self._con.execute(
                "INSERT OR REPLACE INTO traits (id, value) VALUES (?, ?)",
                (trait, new_value),
            )
            self._con.commit()

    @property
    def traits(self) -> dict[str, float]:
        """Current trait values."""
        return dict(self._traits)

    def close(self) -> None:
        """Close the SQLite connection."""
        if self._con:
            self._con.close()
            self._con = None
            log.info("PersonalityEngine closed")
