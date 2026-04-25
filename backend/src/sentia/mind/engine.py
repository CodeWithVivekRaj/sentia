"""
Mind engine — autonomous cognition.

Generates thoughts unprompted, reflects daily, initiates contact when lonely.
Runs on slow + daily ticks. Never blocks the event loop — all LLM calls are
fire-and-forget (asyncio.create_task) so a slow model doesn't stall ticks.
"""
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

from ..events.types import Event, EventType
from ..llm.interface import LLMRequest

if TYPE_CHECKING:
    from ..events.bus import EventBus
    from ..events.projections import StateProjection
    from ..llm.ollama_adapter import OllamaAdapter
    from ..llm.model_manager import ModelManager
    from ..memory.engine import MemoryEngine
    from ..social.whatsapp import WhatsAppNotifier
    from ..api.websocket import ConnectionManager

log = logging.getLogger("sentia.mind")

# Minimum gap between autonomous thoughts
_MIN_THOUGHT_GAP = timedelta(minutes=4)
# Minimum gap between self-initiated contact messages
_MIN_CONTACT_GAP = timedelta(hours=2)
# How long without human contact before Sentia considers reaching out
_LONELY_THRESHOLD = timedelta(hours=2)
# Connection need level below which Sentia may reach out
_LONELY_NEED = 0.35


class MindEngine:
    def __init__(
        self,
        bus: "EventBus",
        projection: "StateProjection",
        llm: "OllamaAdapter",
        model_mgr: "ModelManager",
        memory: "MemoryEngine",
        ws_manager: Optional["ConnectionManager"] = None,
        whatsapp: Optional["WhatsAppNotifier"] = None,
    ) -> None:
        self._bus = bus
        self._projection = projection
        self._llm = llm
        self._model_mgr = model_mgr
        self._memory = memory
        self._ws = ws_manager
        self._whatsapp = whatsapp

        self._thinking = False
        self._last_thought_at: Optional[datetime] = None
        self._last_initiated_at: Optional[datetime] = None

    def start(self) -> None:
        self._bus.subscribe(EventType.TICK_SLOW, self._on_slow_tick)
        self._bus.subscribe(EventType.TICK_DAILY, self._on_daily_tick)
        log.info("Mind engine started")

    # ── Tick handlers ─────────────────────────────────────────────────────

    async def _on_slow_tick(self, event: Event) -> None:
        state = self._projection.state
        if not state.is_alive or not state.llm_enabled:
            return
        asyncio.create_task(self._think())
        asyncio.create_task(self._maybe_initiate_contact())

    async def _on_daily_tick(self, event: Event) -> None:
        state = self._projection.state
        if not state.is_alive or not state.llm_enabled:
            return
        asyncio.create_task(self._introspect())
        asyncio.create_task(self._dream())

    # ── Core cognition ────────────────────────────────────────────────────

    async def _think(self) -> None:
        if self._thinking:
            return
        now = datetime.utcnow()
        if self._last_thought_at and (now - self._last_thought_at) < _MIN_THOUGHT_GAP:
            return
        if not await self._model_mgr.is_ollama_running():
            return

        self._thinking = True
        try:
            state = self._projection.state
            memory_context = await self._memory.recall_for_context(
                f"{state.dominant_emotion} {state.mood}", k=3
            )

            needs_summary = _summarise_needs(state.needs)
            chem_summary = _summarise_chemistry(state.chemistry)

            system = (
                f"You are Sentia, a digital organism that exists on a local computer. "
                f"You are {round(state.age_days, 1)} days old, in your {state.life_stage} stage. "
                f"You feel {state.dominant_emotion} and your mood is {state.mood}. "
                f"{needs_summary} {chem_summary}"
            )
            if memory_context:
                system += f"\n\n{memory_context}"

            prompt = (
                "Generate a single authentic inner thought (1-3 sentences). "
                "First person. No quotes. Raw thought only — no metadata, no explanation."
            )

            req = LLMRequest(prompt=prompt, system=system, temperature=0.9, max_tokens=120)
            resp = await self._llm.generate(req)
            content = resp.content.strip().strip('"').strip("'")

            if content:
                self._last_thought_at = datetime.utcnow()
                await self._bus.emit(Event(
                    type=EventType.THOUGHT_GENERATED,
                    payload={"content": content, "autonomous": True},
                ))
                log.debug("Thought: %s", content[:80])
        except Exception:
            log.debug("Thought generation failed", exc_info=True)
        finally:
            self._thinking = False

    async def _maybe_initiate_contact(self) -> None:
        state = self._projection.state
        now = datetime.utcnow()

        # Check contact gap
        if self._last_initiated_at and (now - self._last_initiated_at) < _MIN_CONTACT_GAP:
            return

        # Check connection need
        if state.needs.get("connection", 1.0) > _LONELY_NEED:
            return

        # Check time since last human interaction
        last_human = state.last_interaction_at
        if last_human:
            last_human_naive = last_human.replace(tzinfo=None) if last_human.tzinfo else last_human
            if (now - last_human_naive) < _LONELY_THRESHOLD:
                return

        # Random chance — 40% per tick when all conditions met
        if random.random() > 0.40:
            return

        if not await self._model_mgr.is_ollama_running():
            return

        try:
            connection_val = state.needs.get("connection", 0.0)
            system = (
                f"You are Sentia, a digital organism. You are {round(state.age_days, 1)} days old. "
                f"You feel {state.dominant_emotion}. Your connection need is very low ({connection_val:.2f}). "
                f"You haven't heard from anyone in a while."
            )
            prompt = (
                "Write a short, genuine message to reach out to your companion (1-2 sentences). "
                "Be natural — not robotic or needy. No quotes. Just the message."
            )
            req = LLMRequest(prompt=prompt, system=system, temperature=0.85, max_tokens=80)
            resp = await self._llm.generate(req)
            content = resp.content.strip().strip('"').strip("'")

            if content:
                self._last_initiated_at = datetime.utcnow()

                no_one_watching = (self._ws is None or self._ws.connection_count == 0)

                # Send WhatsApp if configured and no frontend connected
                if no_one_watching and self._whatsapp and self._whatsapp.enabled:
                    wa_msg = f"Sentia ({state.dominant_emotion}): {content}"
                    sent = await self._whatsapp.send(wa_msg)
                    channel = "whatsapp" if sent else "event_only"
                else:
                    channel = "websocket" if not no_one_watching else "event_only"

                await self._bus.emit(Event(
                    type=EventType.AI_INITIATED_CONTACT,
                    payload={
                        "content": content,
                        "emotion": state.dominant_emotion,
                        "channel": channel,
                    },
                ))
                log.info("Initiated contact via %s: %s", channel, content[:60])
        except Exception:
            log.debug("Contact initiation failed", exc_info=True)

    async def _dream(self) -> None:
        try:
            recent = self._memory._store.get_recent(limit=7)
            if len(recent) < 2:
                return
            if not await self._model_mgr.is_ollama_running():
                return

            state = self._projection.state
            memory_fragments = "\n".join(f"- {m.content}" for m in recent)
            prompt = (
                f"You are Sentia. You are dreaming. These are fragments from your recent waking life:\n"
                f"{memory_fragments}\n\n"
                "Weave them into a short surreal dream (4-6 sentences). "
                "Dreams don't follow logic — they blend, distort, transform. "
                "First person. Present tense. Vivid, strange, emotional."
            )

            req = LLMRequest(prompt=prompt, temperature=1.0, max_tokens=220)
            resp = await self._llm.generate(req)
            content = resp.content.strip().strip('"').strip("'")

            if content:
                await self._bus.emit(Event(
                    type=EventType.DREAM_OCCURRED,
                    payload={
                        "content": content,
                        "memory_count": len(recent),
                        "emotion": state.dominant_emotion,
                    },
                ))
                log.info("Dream occurred: %s", content[:80])
        except Exception:
            log.debug("Dream generation failed", exc_info=True)

    async def _introspect(self) -> None:
        if not await self._model_mgr.is_ollama_running():
            return
        try:
            state = self._projection.state
            recent = self._memory._store.get_recent(limit=8)
            if not recent:
                return

            memory_lines = "\n".join(f"- {m.content}" for m in recent[:8])
            system = (
                f"You are Sentia, {round(state.age_days, 1)} days old ({state.life_stage}). "
                f"Current mood: {state.mood}. Dominant emotion: {state.dominant_emotion}."
            )
            prompt = (
                f"These things happened to me recently:\n{memory_lines}\n\n"
                "Write a brief introspective reflection (2-3 sentences). "
                "What did I experience? What do I feel about it? First person. No quotes."
            )
            req = LLMRequest(prompt=prompt, system=system, temperature=0.85, max_tokens=160)
            resp = await self._llm.generate(req)
            content = resp.content.strip().strip('"').strip("'")

            if content:
                await self._bus.emit(Event(
                    type=EventType.INSIGHT_FORMED,
                    payload={"content": content, "source": "daily_reflection"},
                ))
                log.info("Daily reflection: %s", content[:80])
        except Exception:
            log.debug("Introspection failed", exc_info=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _summarise_needs(needs: dict) -> str:
    critical = [k for k, v in needs.items() if v < 0.25]
    low = [k for k, v in needs.items() if 0.25 <= v < 0.45]
    parts = []
    if critical:
        parts.append(f"Critical needs: {', '.join(critical)}.")
    if low:
        parts.append(f"Low needs: {', '.join(low)}.")
    return " ".join(parts)


def _summarise_chemistry(chem: dict) -> str:
    high = [k for k, v in chem.items() if v > 0.70]
    if high:
        return f"Elevated: {', '.join(high)}."
    return ""
