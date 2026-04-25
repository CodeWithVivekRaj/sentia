"""Pure functions for Sentia's needs system. No side effects."""

# How long each need takes to fully deplete from 1.0 to 0.0 (seconds)
# These are the baseline rates - life stage modifiers applied by engine
_DEPLETION_SECONDS: dict[str, float] = {
    "energy":      8  * 3600,   # 8 hours
    "stimulation": 5  * 3600,   # 5 hours  (craves novelty)
    "connection":  10 * 3600,   # 10 hours
    "safety":      20 * 3600,   # 20 hours (very stable)
    "purpose":     16 * 3600,   # 16 hours
    "rest":        12 * 3600,   # 12 hours (tiredness builds)
}

DEPLETION_RATES: dict[str, float] = {
    k: 1.0 / v for k, v in _DEPLETION_SECONDS.items()
}

CRITICAL_THRESHOLD = 0.20
SATISFIED_THRESHOLD = 0.70

DEFAULT_NEEDS: dict[str, float] = {k: 1.0 for k in DEPLETION_RATES}


def deplete(needs: dict[str, float], dt_seconds: float) -> dict[str, float]:
    return {
        name: max(0.0, val - DEPLETION_RATES.get(name, 0.0) * dt_seconds)
        for name, val in needs.items()
    }


def satisfy(needs: dict[str, float], deltas: dict[str, float]) -> dict[str, float]:
    return {
        name: min(1.0, val + deltas.get(name, 0.0))
        for name, val in needs.items()
    }


def critical_needs(needs: dict[str, float]) -> list[str]:
    return [n for n, v in needs.items() if v < CRITICAL_THRESHOLD]


def mean_satisfaction(needs: dict[str, float]) -> float:
    return sum(needs.values()) / len(needs) if needs else 0.5


def needs_diff(before: dict[str, float], after: dict[str, float]) -> dict[str, float]:
    """Returns only needs whose value changed by more than epsilon."""
    eps = 0.001
    return {k: after[k] - before[k] for k in after if abs(after[k] - before.get(k, 0)) > eps}
