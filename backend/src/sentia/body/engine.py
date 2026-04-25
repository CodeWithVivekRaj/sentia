"""
Body engine — the deterministic core of Sentia.

Runs on every tick. Reads current state, applies pure-function physics,
emits events for every meaningful change. Never stores mutable state
beyond lightweight accumulators for pending boosts between ticks.
"""
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from ..events.types import Event, EventType
from . import needs as N
from . import chemistry as C
from . import emotions as E
from .lifecycle import age_days, life_stage, depletion_multiplier

if TYPE_CHECKING:
    from ..events.bus import EventBus
    from ..events.projections import StateProjection

log = logging.getLogger("sentia.body")

# ── Interaction effects on needs ─────────────────────────────────────────────
_NEED_SATISFACTIONS: dict[EventType, dict[str, float]] = {
    EventType.HUMAN_MESSAGE_RECEIVED: {
        "connection":   0.06,
        "stimulation":  0.04,
        "safety":       0.01,
    },
    EventType.AI_RESPONDED: {
        "purpose":      0.02,
        "stimulation":  0.02,
    },
}

# ── Interaction effects on chemistry ─────────────────────────────────────────
_CHEM_BOOSTS: dict[EventType, dict[str, float]] = {
    EventType.HUMAN_MESSAGE_RECEIVED: {
        "oxytocin":  0.05,
        "dopamine":  0.03,
    },
    EventType.AI_RESPONDED: {
        "dopamine":    0.02,
        "endorphins":  0.01,
    },
}


class BodyEngine:
    """
    Coordinates all deterministic body systems.
    Subscribes to social events to accumulate pending boosts.
    Called by the scheduler on each tick.
    """

    def __init__(self, bus: "EventBus", projection: "StateProjection") -> None:
        self._bus = bus
        self._projection = projection

        # Accumulators reset every fast tick
        self._pending_need_sats: dict[str, float] = {}
        self._pending_chem_boosts: dict[str, float] = {}

        # Trackers to detect changes worth emitting as discrete events
        self._known_critical: set[str] = set()
        self._known_emotions: set[str] = set()
        self._known_mood: str = "neutral"
        self._known_stage: str = "infant"

        # Subscribe to events that affect the body
        for et in _NEED_SATISFACTIONS:
            bus.subscribe(et, self._on_social_event)

    # ── Event subscriptions ───────────────────────────────────────────────

    async def _on_social_event(self, event: Event) -> None:
        for need, delta in _NEED_SATISFACTIONS.get(event.type, {}).items():
            self._pending_need_sats[need] = self._pending_need_sats.get(need, 0.0) + delta
        for chem, delta in _CHEM_BOOSTS.get(event.type, {}).items():
            self._pending_chem_boosts[chem] = self._pending_chem_boosts.get(chem, 0.0) + delta

    # ── Ticks ─────────────────────────────────────────────────────────────

    async def fast_tick(self, dt_seconds: float = 30.0) -> None:
        """Run every 30 s. Updates all body systems."""
        state = self._projection.state
        if not state.is_alive:
            return

        # ── Age & lifecycle ───────────────────────────────────────────────
        born = state.born_at
        age = age_days(born) if born else 0.0
        stage = life_stage(age)
        mult = depletion_multiplier(age)

        # ── Needs ─────────────────────────────────────────────────────────
        effective_dt = dt_seconds * mult
        new_needs = N.deplete(dict(state.needs), effective_dt)

        if self._pending_need_sats:
            new_needs = N.satisfy(new_needs, self._pending_need_sats)
            self._pending_need_sats = {}

        # ── Chemistry ────────────────────────────────────────────────────
        chem_targets = C.targets(new_needs)
        new_chem = C.step(dict(state.chemistry), chem_targets, dt_seconds)

        if self._pending_chem_boosts:
            new_chem = C.boost(new_chem, self._pending_chem_boosts)
            self._pending_chem_boosts = {}

        # ── Emotions ─────────────────────────────────────────────────────
        new_emotions = E.derive(new_chem, new_needs)
        dom = E.dominant(new_emotions)
        new_mood = E.mood(new_chem, new_emotions)

        # ── Emit body snapshot (projection reads this) ────────────────────
        await self._bus.emit(Event(
            type=EventType.TICK_FAST,
            payload={
                "needs":            new_needs,
                "chemistry":        {k: round(v, 4) for k, v in new_chem.items()},
                "emotions":         new_emotions,
                "dominant_emotion": dom,
                "mood":             new_mood,
                "age_days":         round(age, 4),
                "life_stage":       stage,
                "dt_seconds":       dt_seconds,
            },
        ))

        # ── Emit significant discrete events ─────────────────────────────
        await self._emit_significant(new_needs, new_chem, new_emotions, new_mood, stage, age)

    async def slow_tick(self, dt_seconds: float = 300.0) -> None:
        """Run every 5 min."""
        state = self._projection.state
        if not state.is_alive:
            return
        await self._bus.emit(Event(
            type=EventType.TICK_SLOW,
            payload={"timestamp": datetime.utcnow().isoformat(), "dt_seconds": dt_seconds},
        ))

    async def daily_tick(self) -> None:
        """Run once per day. Simulates rest/sleep recovery."""
        state = self._projection.state
        if not state.is_alive:
            return

        log.info("Daily tick — rest recovery")
        await self._bus.emit(Event(
            type=EventType.TICK_DAILY,
            payload={"timestamp": datetime.utcnow().isoformat()},
        ))
        # Partial recovery while Sentia "sleeps"
        await self._bus.emit(Event(
            type=EventType.NEED_SATISFIED,
            payload={"need": "rest",   "delta": 0.60},
        ))
        await self._bus.emit(Event(
            type=EventType.NEED_SATISFIED,
            payload={"need": "energy", "delta": 0.50},
        ))

    # ── Significant event emission ────────────────────────────────────────

    async def _emit_significant(
        self,
        needs: dict,
        chem: dict,
        emotions: dict,
        new_mood: str,
        stage: str,
        age: float,
    ) -> None:
        # Need critical crossings
        now_critical = set(N.critical_needs(needs))

        for need in now_critical - self._known_critical:
            await self._bus.emit(Event(
                type=EventType.NEED_CRITICAL,
                payload={"need": need, "value": round(needs[need], 3)},
            ))
            log.warning("Need critical: %s = %.3f", need, needs[need])

        for need in self._known_critical - now_critical:
            await self._bus.emit(Event(
                type=EventType.NEED_SATISFIED,
                payload={"need": need, "value": round(needs[need], 3), "delta": 0.0},
            ))

        self._known_critical = now_critical

        # Emotion appearances / disappearances
        now_emotions = set(emotions.keys())

        for em in now_emotions - self._known_emotions:
            await self._bus.emit(Event(
                type=EventType.EMOTION_EMERGED,
                payload={"emotion": em, "intensity": emotions[em]},
            ))

        for em in self._known_emotions - now_emotions:
            await self._bus.emit(Event(
                type=EventType.EMOTION_FADED,
                payload={"emotion": em},
            ))

        self._known_emotions = now_emotions

        # Mood shift
        if new_mood != self._known_mood:
            await self._bus.emit(Event(
                type=EventType.MOOD_SHIFTED,
                payload={"mood": new_mood, "previous": self._known_mood},
            ))
            log.info("Mood shifted: %s → %s", self._known_mood, new_mood)
            self._known_mood = new_mood

        # Cortisol spike notification
        prev_cort = self._projection.state.chemistry.get("cortisol", 0.0)
        if chem.get("cortisol", 0.0) > 0.70 and prev_cort <= 0.70:
            await self._bus.emit(Event(
                type=EventType.CORTISOL_SPIKED,
                payload={"level": round(chem["cortisol"], 3)},
            ))

        # Life stage transition
        if stage != self._known_stage:
            await self._bus.emit(Event(
                type=EventType.LIFE_STAGE_CHANGED,
                payload={"stage": stage, "previous": self._known_stage, "age_days": age},
            ))
            log.info("Life stage: %s → %s (%.1f days)", self._known_stage, stage, age)
            self._known_stage = stage

    def initialize_from_state(self) -> None:
        """Sync trackers with current projected state on startup."""
        state = self._projection.state
        self._known_critical = set(N.critical_needs(dict(state.needs)))
        self._known_emotions = set(state.emotions.keys())
        self._known_mood = state.mood
        self._known_stage = state.life_stage
