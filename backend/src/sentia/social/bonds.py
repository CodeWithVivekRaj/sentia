"""Companion bond — tracks relationship strength with the primary human."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from ..events.types import EventType

if TYPE_CHECKING:
    from ..events.bus import EventBus
    from ..events.projections import StateProjection

log = logging.getLogger("sentia.social.bonds")


class BondTracker:
    """Tracks the bond between Sentia and her primary companion."""

    def __init__(self, projection: "StateProjection", companion_name: str) -> None:
        self._projection = projection
        self._companion_name = companion_name
        self._interaction_count: int = 0

    def snapshot(self) -> dict:
        """Compute and return current bond data from projection state."""
        state = self._projection.state
        count = self._interaction_count

        # Bond strength: interaction volume (70%) + oxytocin level (30%)
        oxytocin = state.chemistry.get("oxytocin", 0.3)
        interaction_factor = min(1.0, count / 150) * 0.7
        chemistry_factor = oxytocin * 0.3
        bond_strength = round(interaction_factor + chemistry_factor, 3)

        # Relationship stage
        if count < 5:
            relationship = "new"
        elif count < 30:
            relationship = "forming"
        elif count < 100:
            relationship = "established"
        else:
            relationship = "deep"

        first_contact = state.born_at.isoformat() if state.born_at else None
        last_contact = (
            state.last_interaction_at.isoformat()
            if state.last_interaction_at
            else None
        )

        return {
            "name": self._companion_name,
            "interaction_count": count,
            "bond_strength": bond_strength,
            "first_contact": first_contact,
            "last_contact": last_contact,
            "relationship": relationship,
        }

    def start(self, bus: "EventBus") -> None:
        """Subscribe to interaction events on the bus."""
        bus.subscribe(EventType.HUMAN_MESSAGE_RECEIVED, self._on_interaction)
        bus.subscribe(EventType.AI_INITIATED_CONTACT, self._on_interaction)
        log.info("BondTracker started — tracking companion '%s'", self._companion_name)

    async def _on_interaction(self, event) -> None:  # noqa: ARG002
        self._interaction_count += 1
