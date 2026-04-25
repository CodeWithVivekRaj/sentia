"""SQLite-backed memory store with cosine similarity retrieval."""
import json
import logging
import math
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

from .types import Memory

log = logging.getLogger("sentia.memory.store")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    source_event_type TEXT NOT NULL,
    emotion TEXT NOT NULL,
    emotion_intensity REAL NOT NULL,
    mood TEXT NOT NULL,
    needs_snapshot TEXT NOT NULL,
    embedding TEXT NOT NULL,
    formed_at TEXT NOT NULL,
    salience REAL NOT NULL,
    strength REAL NOT NULL,
    last_recalled_at TEXT,
    recall_count INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_memories_formed_at ON memories(formed_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_emotion ON memories(emotion);
CREATE INDEX IF NOT EXISTS idx_memories_strength ON memories(strength);
"""


class MemoryStore:
    def __init__(self, db_path: str) -> None:
        self._path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def initialize(self) -> None:
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        log.info("Memory store initialised at %s", self._path)

    def store(self, memory: Memory) -> None:
        assert self._conn
        self._conn.execute(
            """INSERT INTO memories
               (id, content, source_event_id, source_event_type, emotion,
                emotion_intensity, mood, needs_snapshot, embedding, formed_at,
                salience, strength, last_recalled_at, recall_count)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                memory.id,
                memory.content,
                memory.source_event_id,
                memory.source_event_type,
                memory.emotion,
                memory.emotion_intensity,
                memory.mood,
                json.dumps(memory.needs_snapshot),
                json.dumps(memory.embedding),
                memory.formed_at.isoformat(),
                memory.salience,
                memory.strength,
                memory.last_recalled_at.isoformat() if memory.last_recalled_at else None,
                memory.recall_count,
            ),
        )
        self._conn.commit()

    def recall(
        self,
        query_embedding: list[float],
        limit: int = 5,
        min_strength: float = 0.05,
    ) -> list[tuple[Memory, float]]:
        """Return top-k memories by cosine similarity, filtered by strength."""
        assert self._conn
        rows = self._conn.execute(
            "SELECT * FROM memories WHERE strength >= ? ORDER BY formed_at DESC LIMIT 500",
            (min_strength,),
        ).fetchall()

        if not rows or not query_embedding:
            return []

        q = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return []
        q = q / q_norm

        scored: list[tuple[Memory, float]] = []
        for row in rows:
            emb = json.loads(row["embedding"])
            if not emb:
                continue
            v = np.array(emb, dtype=np.float32)
            v_norm = np.linalg.norm(v)
            if v_norm == 0:
                continue
            sim = float(np.dot(q, v / v_norm))
            scored.append((_row_to_memory(row), sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    def get_recent(self, limit: int = 20) -> list[Memory]:
        assert self._conn
        rows = self._conn.execute(
            "SELECT * FROM memories ORDER BY formed_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [_row_to_memory(r) for r in rows]

    def get_all(self, limit: int = 50, offset: int = 0) -> list[Memory]:
        assert self._conn
        rows = self._conn.execute(
            "SELECT * FROM memories ORDER BY formed_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [_row_to_memory(r) for r in rows]

    def count(self) -> int:
        assert self._conn
        return self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    def decay_all(self, dt_hours: float) -> int:
        """Apply Ebbinghaus exponential decay. Returns count of forgotten memories."""
        assert self._conn
        rows = self._conn.execute("SELECT id, salience, strength FROM memories WHERE strength > 0.05").fetchall()
        forgotten = 0
        for row in rows:
            # Stability increases with salience: high-salience memories decay slower
            stability_hours = 24.0 + row["salience"] * 72.0  # 24h–96h half-life
            new_strength = row["strength"] * math.exp(-dt_hours / stability_hours)
            if new_strength < 0.05:
                new_strength = 0.0
                forgotten += 1
            self._conn.execute(
                "UPDATE memories SET strength = ? WHERE id = ?",
                (new_strength, row["id"]),
            )
        self._conn.commit()
        return forgotten

    def reinforce(self, memory_id: str, boost: float = 0.2) -> None:
        """Recalling a memory strengthens it (spaced repetition)."""
        assert self._conn
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            """UPDATE memories
               SET strength = MIN(1.0, strength + ?),
                   recall_count = recall_count + 1,
                   last_recalled_at = ?
               WHERE id = ?""",
            (boost, now, memory_id),
        )
        self._conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()


def _row_to_memory(row: sqlite3.Row) -> Memory:
    return Memory(
        id=row["id"],
        content=row["content"],
        source_event_id=row["source_event_id"],
        source_event_type=row["source_event_type"],
        emotion=row["emotion"],
        emotion_intensity=row["emotion_intensity"],
        mood=row["mood"],
        needs_snapshot=json.loads(row["needs_snapshot"]),
        embedding=json.loads(row["embedding"]),
        formed_at=datetime.fromisoformat(row["formed_at"]),
        salience=row["salience"],
        strength=row["strength"],
        last_recalled_at=datetime.fromisoformat(row["last_recalled_at"]) if row["last_recalled_at"] else None,
        recall_count=row["recall_count"],
    )
