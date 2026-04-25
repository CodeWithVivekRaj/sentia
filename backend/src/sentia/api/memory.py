"""Memory API — browse and search Sentia's memories."""
from fastapi import APIRouter, HTTPException, Query
from . import deps

router = APIRouter(tags=["memory"])


@router.get("/memories")
async def list_memories(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    mem = deps.memory_engine
    if not mem:
        return {"memories": [], "total": 0}
    memories = mem._store.get_all(limit=limit, offset=offset)
    total = mem._store.count()
    return {
        "memories": [m.to_dict() for m in memories],
        "total": total,
    }


@router.get("/memories/recall")
async def recall_memories(q: str = Query(..., min_length=1), k: int = Query(5, ge=1, le=20)):
    mem = deps.memory_engine
    if not mem:
        return {"memories": [], "query": q}
    embedding = await mem._embedder.embed(q)
    results = mem._store.recall(embedding, limit=k)
    return {
        "query": q,
        "memories": [
            {**m.to_dict(), "similarity": round(sim, 4)}
            for m, sim in results
        ],
    }


@router.get("/memories/stats")
async def memory_stats():
    mem = deps.memory_engine
    if not mem:
        return {"total": 0, "embedding_dim": None}
    return {
        "total": mem._store.count(),
        "embedding_dim": mem._embedder.dim,
    }
