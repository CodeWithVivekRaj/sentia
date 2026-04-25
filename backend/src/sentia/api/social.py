from fastapi import APIRouter
from . import deps

router = APIRouter(prefix="/social", tags=["social"])


@router.get("/bond")
async def get_bond():
    bt = deps.bond_tracker  # set by main.py
    if not bt:
        return {"companion": None}
    return {"companion": bt.snapshot()}
