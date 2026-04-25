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
from ..mind.engine import MindEngine
from ..social.whatsapp import WhatsAppNotifier
from ..social.bonds import BondTracker
from ..self.personality import PersonalityEngine
from ..rewards.engine import RewardEngine
from .websocket import ConnectionManager
from . import deps
from .health import router as health_router
from .models import router as models_router
from .state import router as state_router
from .chat import router as chat_router
from .ws_router import router as ws_router
from .memory import router as memory_router
from .notify import router as notify_router
from .dreams import router as dreams_router
from .self_api import router as self_api_router
from .rewards_api import router as rewards_router
from .social import router as social_router
from .chronicle import router as chronicle_router

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

    # ── WhatsApp notifier ────────────────────────────────────────────────
    wa = WhatsAppNotifier(
        provider=settings.whatsapp_provider,
        phone=settings.whatsapp_phone,
        api_key=settings.whatsapp_api_key,
        account_sid=settings.twilio_account_sid,
        auth_token=settings.twilio_auth_token,
        from_number=settings.twilio_from,
        to_number=settings.twilio_to,
    )
    deps.whatsapp = wa
    log.info("WhatsApp notifier: provider=%s enabled=%s", wa.provider, wa.enabled)

    # ── Personality engine ───────────────────────────────────────────────
    personality_db = str(Path(settings.db_path).parent / "personality.db")
    personality = PersonalityEngine()
    personality.initialize(personality_db, genome_seed="default")
    personality.start(bus)
    deps.personality_engine = personality
    log.info("Personality engine started")

    # ── Reward engine ────────────────────────────────────────────────────
    reward_eng = RewardEngine(settings.rewards_dir, bus)
    reward_eng.start()
    deps.reward_engine = reward_eng
    log.info("Reward engine started (%d rewards loaded)", len(reward_eng.definitions))

    # ── Bond tracker ─────────────────────────────────────────────────────
    bond = BondTracker(projection=projection, companion_name=settings.companion_name)
    bond.start(bus)
    deps.bond_tracker = bond
    log.info("Bond tracker started (companion=%s)", settings.companion_name)

    # ── Mind engine ──────────────────────────────────────────────────────
    mind = MindEngine(bus, projection, adapter, model_mgr, mem_engine, ws_mgr, wa)
    mind.start()
    deps.mind_engine = mind
    log.info("Mind engine started")

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
    await wa.close()
    personality.close()
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
app.include_router(notify_router, prefix="/api")
app.include_router(dreams_router, prefix="/api")
app.include_router(self_api_router, prefix="/api")
app.include_router(rewards_router, prefix="/api")
app.include_router(social_router, prefix="/api")
app.include_router(chronicle_router, prefix="/api")
app.include_router(ws_router)


@app.get("/")
async def root():
    return {"name": "Sentia", "status": "alive", "docs": "/docs"}


def start():
    import uvicorn
    uvicorn.run("sentia.api.main:app", host=settings.host, port=settings.port, reload=settings.debug)


if __name__ == "__main__":
    start()
