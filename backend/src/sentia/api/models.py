"""Model management endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
from . import deps

router = APIRouter(prefix="/models", tags=["models"])


class SetModelRequest(BaseModel):
    model: str


class PullModelRequest(BaseModel):
    model: str


@router.get("")
async def list_models():
    if not deps.model_manager:
        raise HTTPException(503, "Model manager not initialized")
    models = await deps.model_manager.list_models()
    return {
        "models": [
            {
                "name": m.name,
                "size_gb": m.size_gb,
                "vram_estimate_gb": m.vram_estimate_gb,
                "fits_in_vram": m.fits_in_vram,
                "is_installed": m.is_installed,
                "digest": m.digest,
            }
            for m in models
        ],
        "available_vram_gb": 6.0,
        "ollama_running": await deps.model_manager.is_ollama_running(),
        "ollama_version": await deps.model_manager.get_version(),
    }


@router.post("/select")
async def select_model(req: SetModelRequest):
    if not deps.llm_adapter:
        raise HTTPException(503, "LLM adapter not initialized")
    deps.llm_adapter.set_model(req.model)
    from ..events.types import Event, EventType
    from datetime import datetime
    event = Event(
        type=EventType.MODEL_CHANGED,
        payload={"model": req.model},
    )
    persisted = await deps.event_bus.emit(event)
    return {"selected": req.model, "event_id": persisted.id}


@router.post("/pull")
async def pull_model(req: PullModelRequest):
    """Stream pull progress as Server-Sent Events."""
    if not deps.model_manager:
        raise HTTPException(503, "Model manager not initialized")

    async def generate():
        async for progress in deps.model_manager.pull_model(req.model):
            yield f"data: {json.dumps(progress)}\n\n"
        yield "data: {\"status\": \"complete\"}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
