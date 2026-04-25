from fastapi import APIRouter
from . import deps

router = APIRouter(prefix="/rewards", tags=["rewards"])


@router.get("")
async def list_rewards():
    re = deps.reward_engine
    if not re:
        return {"rewards": []}
    return {"rewards": re.definitions}
