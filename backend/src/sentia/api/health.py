"""Health check endpoint."""
from fastapi import APIRouter
from . import deps
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health():
    ollama_ok = await deps.model_manager.is_ollama_running() if deps.model_manager else False
    event_count = await deps.event_store.count() if deps.event_store else 0
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "ollama": ollama_ok,
        "event_count": event_count,
        "ws_connections": deps.ws_manager.connection_count if deps.ws_manager else 0,
        "sentia_alive": deps.state_projection.state.is_alive if deps.state_projection else False,
    }
