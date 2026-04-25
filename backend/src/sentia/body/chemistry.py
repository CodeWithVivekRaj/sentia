"""Pure functions for neurochemistry. All values normalized 0.0–1.0."""

# How fast each chemical moves toward its target value (fraction per second)
# Fast = reward circuits (dopamine, adrenaline)
# Slow = mood stabilisers (serotonin, melatonin)
ADAPTATION_RATES: dict[str, float] = {
    "dopamine":   0.0025,
    "serotonin":  0.0008,
    "cortisol":   0.0015,
    "oxytocin":   0.0012,
    "endorphins": 0.0010,
    "adrenaline": 0.0030,
    "melatonin":  0.0005,
}

DEFAULT_CHEMISTRY: dict[str, float] = {
    "dopamine":   0.50,
    "serotonin":  0.50,
    "cortisol":   0.20,
    "oxytocin":   0.30,
    "endorphins": 0.30,
    "adrenaline": 0.10,
    "melatonin":  0.10,
}


def targets(needs: dict[str, float]) -> dict[str, float]:
    """
    Derive target chemistry levels from current needs.
    Each target is a weighted blend of need satisfaction values.
    Pure function — no side effects.
    """
    e  = needs.get("energy",      0.5)
    st = needs.get("stimulation", 0.5)
    c  = needs.get("connection",  0.5)
    sf = needs.get("safety",      0.5)
    p  = needs.get("purpose",     0.5)
    r  = needs.get("rest",        0.5)

    return {
        # Dopamine: reward/novelty — driven by stimulation + purpose + energy
        "dopamine":   _clamp(st * 0.55 + p * 0.30 + e * 0.15),

        # Serotonin: wellbeing — safety + connection + purpose
        "serotonin":  _clamp(sf * 0.40 + c * 0.35 + p * 0.25),

        # Cortisol: stress — rises when energy/safety/rest are low
        "cortisol":   _clamp((1 - sf) * 0.40 + (1 - e) * 0.35 + (1 - r) * 0.25),

        # Oxytocin: bonding — driven almost entirely by connection
        "oxytocin":   _clamp(c * 0.80 + sf * 0.20),

        # Endorphins: activity/pleasure — energy + stimulation
        "endorphins": _clamp(e * 0.60 + st * 0.40),

        # Adrenaline: arousal/threat — mirrors cortisol but faster-spiking
        "adrenaline": _clamp((1 - sf) * 0.50 + (1 - e) * 0.30 + (1 - r) * 0.20) * 0.75,

        # Melatonin: tiredness/circadian — rises when rest + energy are low
        "melatonin":  _clamp((1 - r) * 0.55 + (1 - e) * 0.45) * 0.85,
    }


def step(
    chemistry: dict[str, float],
    target: dict[str, float],
    dt_seconds: float,
) -> dict[str, float]:
    """Move chemistry values toward targets using exponential approach."""
    result = {}
    for name, current in chemistry.items():
        t = target.get(name, current)
        rate = ADAPTATION_RATES.get(name, 0.001)
        delta = (t - current) * rate * dt_seconds
        result[name] = _clamp(current + delta)
    return result


def boost(chemistry: dict[str, float], deltas: dict[str, float]) -> dict[str, float]:
    """Apply an immediate chemistry impulse (from rewards, events)."""
    return {
        name: _clamp(val + deltas.get(name, 0.0))
        for name, val in chemistry.items()
    }


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))
