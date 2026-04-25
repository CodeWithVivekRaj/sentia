"""Sentia FastAPI application - wires all components together."""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import settings
from ..events.store import EventStore
from ..events.bus import EventBus
from ..events.projections import StateProjection
from ..events.types import Event, EventType
from ..llm.model_manager import ModelManager
from ..llm.ollama_adapter import OllamaAdapter
from ..body.engine import BodyEngine
from ..scheduler.coordinator import TickCoordinator
from ..memory.store import MemoryStore
from ..memory.embedder import Embedder
from ..memory.engine import MemoryEngine
from .websocket import ConnectionManager
from . import deps
from .health import router as health_router
from .models import router as models_router
from .state import router as state_router
from .chat import router as chat_router
from .ws_router import router as ws_router
from .memory import router as memory_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("sentia")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────
    log.info("Sentia starting up...")

    # Ensure data directories exist
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)

    # Event store
    store = EventStore(settings.db_path)
    await store.initialize()
    deps.event_store = store

    # State projection
    projection = StateProjection()
    deps.state_projection = projection

    # Replay existing events to rebuild state
    events = await store.get_since(sequence=0, limit=10000)
    for e in events:
        projection.apply(e)
    log.info(f"Replayed {len(events)} events from store")

    # WebSocket manager
    ws_mgr = ConnectionManager()
    deps.ws_manager = ws_mgr

    # Event bus - registers projection + WS broadcast as handlers
    bus = EventBus(store)

    async def on_event(event: Event):
        projection.apply(event)
        await ws_mgr.broadcast({
            "type": "event",
            "data": event.to_dict(),
            "state": projection.snapshot(),
        })

    bus.subscribe(None, on_event)  # wildcard - all events
    await bus.start()
    deps.event_bus = bus

    # LLM
    model_mgr = ModelManager(settings.ollama_base_url)
    deps.model_manager = model_mgr

    # Use the model from projected state (persisted across restarts)
    current_model = projection.state.current_model or settings.default_model
    adapter = OllamaAdapter(settings.ollama_base_url, current_model)
    deps.llm_adapter = adapter

    ollama_ok = await model_mgr.is_ollama_running()
    log.info(f"Ollama {'available' if ollama_ok else 'NOT available'} at {settings.ollama_base_url}")

    # Birth Sentia if this is a fresh start
    if not projection.state.is_alive:
        birth = Event(
            type=EventType.AI_BORN,
            payload={
                "name": "Sentia",
                "version": "0.1.0",
                "genome_seed": "default",
            },
        )
        await bus.emit(birth)
        log.info("Sentia was born!")

    # Emit system started
    await bus.emit(Event(
        type=EventType.SYSTEM_STARTED,
        payload={"timestamp": datetime.utcnow().isoformat()},
    ))

    log.info(f"Sentia alive. LLM: {projection.state.llm_enabled}, model: {projection.state.current_model}")

    # ── Memory engine ────────────────────────────────────────────────────
    mem_store = MemoryStore(settings.memory_db_path)
    mem_store.initialize()

    embedder = Embedder(settings.ollama_base_url, current_model)

    mem_engine = MemoryEngine(bus, projection, mem_store, embedder)
    mem_engine.start()
    deps.memory_engine = mem_engine
    log.info("Memory engine started (store=%s)", settings.memory_db_path)

    # ── Body engine + scheduler ───────────────────────────────────────────
    body = BodyEngine(bus, projection)
    body.initialize_from_state()

    scheduler = TickCoordinator(body)
    scheduler.setup(
        fast_interval=settings.fast_tick_interval,
        slow_interval=settings.slow_tick_interval,
        daily_interval=settings.daily_tick_interval,
    )
    scheduler.start()
    log.info("Body engine running. First tick in %ds.", settings.fast_tick_interval)

    yield  # ── Running ──

    # ── Shutdown ─────────────────────────────────────────────────────────
    log.info("Sentia shutting down...")
    scheduler.stop()
    await bus.emit(Event(
        type=EventType.SYSTEM_STOPPED,
        payload={"timestamp": datetime.utcnow().isoformat()},
    ))
    await bus.stop()
    await store.close()
    await model_mgr.close()
    await adapter.close()
    mem_store.close()
    await embedder.close()
    log.info("Shutdown complete.")


app = FastAPI(
    title="Sentia",
    description="A Digital Organism",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(models_router, prefix="/api")
app.include_router(state_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(ws_router)


@app.get("/")
async def root():
    return {"name": "Sentia", "status": "alive", "docs": "/docs"}


def start():
    import uvicorn
    uvicorn.run("sentia.api.main:app", host=settings.host, port=settings.port, reload=settings.debug)


if __name__ == "__main__":
    start()
