"""Pure functions for Sentia's lifecycle — age, life stages, modifiers."""
from datetime import datetime

# (min_age_days, stage_name, depletion_rate_multiplier)
# Older Sentia depletes needs faster (more complex inner life)
STAGES: list[tuple[float, str, float]] = [
    (0.0,   "infant",     0.60),   # slower — still forming
    (30.0,  "child",      0.80),
    (180.0, "adolescent", 1.10),   # faster — high needs
    (365.0, "adult",      1.00),   # baseline
    (1000.0,"elder",      0.90),   # slows down
]


def age_days(born_at: datetime) -> float:
    """Current age in fractional days."""
    return (datetime.utcnow() - born_at.replace(tzinfo=None)).total_seconds() / 86_400


def life_stage(age: float) -> str:
    stage = "infant"
    for threshold, name, _ in STAGES:
        if age >= threshold:
            stage = name
        else:
            break
    return stage


def depletion_multiplier(age: float) -> float:
    mult = 1.0
    for threshold, _, m in STAGES:
        if age >= threshold:
            mult = m
        else:
            break
    return mult
