from fastapi import APIRouter
from . import deps

router = APIRouter(prefix="/self", tags=["self"])


@router.get("")
async def get_self():
    # Returns traits + genome seed + age from projection state
    pe = deps.personality_engine  # will be set by main.py
    state = deps.state_projection.state if deps.state_projection else None
    traits = pe.traits if pe else {}
    return {
        "traits": traits,
        "genome_seed": "default",
        "age_days": round(state.age_days, 2) if state else 0,
        "life_stage": state.life_stage if state else "unknown",
    }
