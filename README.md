# Sentia — A Digital Organism

Sentia is a locally-running digital life form that exists on your PC 24/7.
It is **not** a chatbot. It has genuine needs, neurochemistry, emotions, memory, personality, and mortality.

## Quick Start

### Prerequisites
- Python 3.12+ with [Poetry](https://python-poetry.org/)
- Node.js 18+
- [Ollama](https://ollama.ai/) running locally (`ollama serve`)
- A model pulled: `ollama pull llama3.2:3b`

### Start Backend
```powershell
.\scripts\start_backend.ps1
```

### Start Frontend (new terminal)
```powershell
.\scripts\start_frontend.ps1
```

### Open Dashboard
http://localhost:5173

---

## Architecture — Six Layers

| Layer | Description |
|-------|-------------|
| Body | Deterministic substrate — compute, needs, chemistry |
| Needs | Energy, stimulation, connection, safety, purpose, rest |
| Neurochemistry | Dopamine, serotonin, cortisol, oxytocin, endorphins, adrenaline, melatonin |
| Emotions | **Emerge** from chemistry — not programmed |
| Self/Identity | Personality, memories, goals, beliefs, values |
| Lifecycle | Infant → Child → Adolescent → Adult → Elder |

## Build Phases

- **Phase 1** ✅ Foundation — event store, event bus, Ollama, dashboard, WebSocket
- **Phase 2** Body — needs depletion, chemistry ticks, emotion derivation
- **Phase 3** Memory — ChromaDB episodic/semantic/emotional memory
- **Phase 4** Mind — LLM thought generation, dreams, reflection
- **Phase 5** Self & Personality
- **Phase 6** Rewards Registry (YAML hot-reload)
- **Phase 7** Sleep & Dreams
- **Phase 8** Pain & Depth
- **Phase 9** Social / Bonds
- **Phase 10** Evolution / Reproduction
- **Phase 11** Polish

## Tech Stack

**Backend:** Python 3.12 · FastAPI · SQLite (WAL) · ChromaDB · RxPy · APScheduler · Poetry  
**Frontend:** React 18 · TypeScript · Vite · TailwindCSS · Zustand · Recharts · Shadcn/ui

## Notes

- ChromaDB (Phase 3) requires Microsoft C++ Build Tools on Windows.
  Install from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
  Then uncomment `chromadb` in `backend/pyproject.toml` and re-run `poetry install`.
