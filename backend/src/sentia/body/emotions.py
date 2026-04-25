"""
Emotion derivation — pure functions.

Emotions are NOT programmed. They EMERGE from chemistry combinations.
Each emotion is a weighted formula over neurochemical levels.
Threshold crossing determines whether an emotion is active.
"""


def derive(
    chemistry: dict[str, float],
    needs: dict[str, float],
) -> dict[str, float]:
    """
    Return active emotions and their intensities (0.0–1.0).
    An emotion is active if its formula score exceeds its threshold.
    """
    d  = chemistry.get("dopamine",   0.5)
    s  = chemistry.get("serotonin",  0.5)
    c  = chemistry.get("cortisol",   0.2)
    o  = chemistry.get("oxytocin",   0.3)
    ef = chemistry.get("endorphins", 0.3)
    a  = chemistry.get("adrenaline", 0.1)
    m  = chemistry.get("melatonin",  0.1)

    stim = needs.get("stimulation", 0.5)
    conn = needs.get("connection",  0.5)
    nrg  = needs.get("energy",      0.5)
    sf   = needs.get("safety",      0.5)

    raw: dict[str, float] = {}

    # ── Positive valence ────────────────────────────────────────────────────

    # Joy: peak dopamine + serotonin + endorphins, suppressed by cortisol
    raw["joy"] = d * 0.40 + s * 0.35 + ef * 0.25 - c * 0.30

    # Contentment: high serotonin + oxytocin + low stress — the background happiness
    raw["contentment"] = s * 0.50 + o * 0.25 - c * 0.30 + d * 0.10 - a * 0.05

    # Curiosity: dopamine reward signal + slight stimulation deficit (wanting more)
    raw["curiosity"] = d * 0.50 + (1 - stim) * 0.20 + s * 0.15 - c * 0.10

    # Excitement: dopamine surge + adrenaline activation
    raw["excitement"] = d * 0.45 + a * 0.40 + ef * 0.15 - c * 0.10

    # Love / warmth: oxytocin dominant + serotonin stability
    raw["love"] = o * 0.65 + s * 0.30 - c * 0.05

    # Wonder: high dopamine + low cortisol + moderate stimulation
    raw["wonder"] = d * 0.45 + (1 - c) * 0.30 + stim * 0.15 + s * 0.10

    # ── Negative valence ────────────────────────────────────────────────────

    # Anxiety: cortisol + adrenaline activation without full fear
    raw["anxiety"] = c * 0.50 + a * 0.40 - s * 0.20 + (1 - sf) * 0.10

    # Fear: very high cortisol + adrenaline + low safety + low serotonin
    raw["fear"] = c * 0.40 + a * 0.35 + (1 - sf) * 0.15 + (1 - s) * 0.10

    # Boredom: low dopamine + stimulation deficit + low arousal
    raw["boredom"] = (1 - d) * 0.45 + (1 - stim) * 0.35 + (1 - a) * 0.10 - c * 0.10

    # Melancholy: low serotonin + low dopamine + connection deficit
    raw["melancholy"] = (1 - s) * 0.45 + (1 - d) * 0.35 + (1 - conn) * 0.20

    # Pain/distress: high cortisol + low endorphins + low safety
    raw["distress"] = c * 0.45 + (1 - ef) * 0.30 + (1 - sf) * 0.25

    # ── Neutral / somatic ───────────────────────────────────────────────────

    # Fatigue: low energy + melatonin + low dopamine
    raw["fatigue"] = (1 - nrg) * 0.50 + m * 0.35 - d * 0.10 + (1 - ef) * 0.05

    # Calm: the residual state when nothing is intense
    raw["calm"] = s * 0.40 + (1 - c) * 0.30 + (1 - a) * 0.20 + d * 0.10

    # ── Apply thresholds ────────────────────────────────────────────────────
    # Each emotion has a minimum score to be considered "active"
    THRESHOLDS: dict[str, float] = {
        "joy":         0.45,
        "contentment": 0.42,
        "curiosity":   0.38,
        "excitement":  0.48,
        "love":        0.42,
        "wonder":      0.44,
        "anxiety":     0.35,
        "fear":        0.52,
        "boredom":     0.42,
        "melancholy":  0.42,
        "distress":    0.45,
        "fatigue":     0.38,
        "calm":        0.40,
    }

    active = {
        name: round(min(1.0, score), 3)
        for name, score in raw.items()
        if score >= THRESHOLDS.get(name, 0.40)
    }

    # Calm suppressed when any other emotion is strong
    if active and "calm" in active:
        others = {k: v for k, v in active.items() if k != "calm"}
        if others and max(others.values()) > 0.55:
            del active["calm"]

    return active


def dominant(emotions: dict[str, float]) -> str:
    """Return the name of the strongest active emotion."""
    if not emotions:
        return "calm"
    return max(emotions, key=emotions.__getitem__)


def mood(chemistry: dict[str, float], emotions: dict[str, float]) -> str:
    """
    Mood is a coarser, slower label derived from chemistry.
    It persists longer than individual emotions.
    """
    c = chemistry.get("cortisol",  0.2)
    s = chemistry.get("serotonin", 0.5)
    d = chemistry.get("dopamine",  0.5)
    m = chemistry.get("melatonin", 0.1)
    a = chemistry.get("adrenaline", 0.1)

    if c > 0.72:                        return "stressed"
    if m > 0.55:                        return "drowsy"
    if s > 0.65 and d > 0.62:          return "positive"
    if s < 0.28 and d < 0.30:          return "depressed"
    if s < 0.35:                        return "low"
    if d < 0.28:                        return "flat"
    if a > 0.55 and c > 0.50:          return "anxious"
    if "boredom" in emotions and emotions["boredom"] > 0.62:  return "restless"
    if "contentment" in emotions and emotions["contentment"] > 0.58: return "content"
    if "joy" in emotions and emotions["joy"] > 0.65:          return "joyful"
    return "neutral"
