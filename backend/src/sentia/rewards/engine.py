"""Reward engine — loads YAML definitions, fires chemistry boosts when events trigger rewards."""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from ..events.types import Event, EventType

if TYPE_CHECKING:
    from ..events.bus import EventBus

log = logging.getLogger("sentia.rewards")

# Map chemistry key names (as used in YAML) to EventType
_CHEM_EVENT_MAP: dict[str, EventType] = {
    "dopamine":   EventType.DOPAMINE_RELEASED,
    "serotonin":  EventType.SEROTONIN_CHANGED,
    "endorphins": EventType.ENDORPHIN_RELEASED,
    "oxytocin":   EventType.OXYTOCIN_INCREASED,
    "cortisol":   EventType.CORTISOL_SPIKED,
    "adrenaline": EventType.ADRENALINE_SPIKED,
    "melatonin":  EventType.MELATONIN_RISING,
}


class RewardEngine:
    """Loads reward definitions from YAML and fires chemistry boost events on matching triggers."""

    def __init__(self, rewards_dir: str, bus: "EventBus", llm_adapter=None) -> None:
        self._rewards_dir = rewards_dir
        self._bus = bus
        self._llm_adapter = llm_adapter
        self._definitions: list[dict] = []
        self._last_triggered: dict[str, datetime] = {}

    # ── Loading ────────────────────────────────────────────────────────────

    def load_definitions(self) -> list[dict]:
        """Load all *.yaml files from rewards_dir and return a flat list of reward dicts."""
        path = Path(self._rewards_dir)
        if not path.exists():
            log.warning("Rewards directory not found: %s", self._rewards_dir)
            return []

        rewards: list[dict] = []
        for yaml_file in sorted(path.glob("*.yaml")):
            try:
                text = yaml_file.read_text(encoding="utf-8")
                data = yaml.safe_load(text) or {}
                file_rewards = data.get("rewards", [])
                # Annotate each reward with its source file (stem = "social" / "cognitive")
                for r in file_rewards:
                    r.setdefault("_source", yaml_file.stem)
                rewards.extend(file_rewards)
                log.debug("Loaded %d rewards from %s", len(file_rewards), yaml_file.name)
            except Exception as exc:
                log.error("Failed to load %s: %s", yaml_file.name, exc)

        return rewards

    # ── Startup ────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Load definitions and subscribe to trigger events on the bus."""
        self._definitions = self.load_definitions()

        for reward in self._definitions:
            trigger_str: str = reward.get("trigger", "")
            try:
                event_type = EventType(trigger_str)
            except ValueError:
                log.warning(
                    "Reward '%s' references unknown trigger '%s' — skipping",
                    reward.get("id", "?"),
                    trigger_str,
                )
                continue

            handler = self._make_handler(reward)
            self._bus.subscribe(event_type, handler)

        log.info("Reward engine started — %d rewards loaded", len(self._definitions))

    # ── Handler factory ────────────────────────────────────────────────────

    def _make_handler(self, reward: dict):
        """Return an async event handler that applies chemistry boosts with cooldown enforcement."""
        reward_id: str = reward["id"]
        reward_name: str = reward.get("name", reward_id)
        cooldown = timedelta(seconds=int(reward.get("cooldown_seconds", 0)))
        chemistry_boost: dict[str, float] = reward.get("chemistry_boost") or {}

        async def handler(event: Event) -> None:
            now = datetime.utcnow()
            last = self._last_triggered.get(reward_id)
            if last is not None and (now - last) < cooldown:
                return  # still in cooldown

            # Fire one chemistry event per boost key
            for chem_key, delta in chemistry_boost.items():
                try:
                    chem_event_type = _CHEM_EVENT_MAP.get(chem_key)
                    if chem_event_type is None:
                        log.warning("Unknown chemistry key '%s' in reward '%s'", chem_key, reward_id)
                        continue
                    boost_event = Event(
                        type=chem_event_type,
                        payload={"delta": delta, "source": reward_id},
                    )
                    await self._bus.emit(boost_event)
                except Exception as exc:
                    log.error("Failed to emit chemistry event for reward '%s': %s", reward_id, exc)

            self._last_triggered[reward_id] = now
            log.debug("Reward fired: %s", reward_name)

        return handler

    # ── Public API ─────────────────────────────────────────────────────────

    @property
    def definitions(self) -> list[dict]:
        """Return the list of loaded reward definitions (excluding internal _source annotation)."""
        return [
            {k: v for k, v in r.items() if not k.startswith("_")}
            for r in self._definitions
        ]

    async def daily_stats(self, event_store) -> dict:
        """Return approximate daily reward stats. Placeholder implementation."""
        # Future: query event_store for chemistry events with matching source fields
        return {"total_rewards_today": 0}
