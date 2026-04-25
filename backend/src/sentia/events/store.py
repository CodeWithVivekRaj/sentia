"""Append-only SQLite event store with WAL mode."""
import json
import asyncio
from datetime import datetime
from typing import Optional, AsyncIterator
import aiosqlite
from .types import Event, EventType


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS events (
    sequence    INTEGER PRIMARY KEY AUTOINCREMENT,
    id          TEXT NOT NULL UNIQUE,
    type        TEXT NOT NULL,
    payload     TEXT NOT NULL,
    timestamp   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
"""


class EventStore:
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        # WAL mode for concurrent reads
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA synchronous=NORMAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        for stmt in CREATE_TABLE_SQL.strip().split(";"):
            if stmt.strip():
                await self._db.execute(stmt)
        await self._db.commit()

    async def append(self, event: Event) -> Event:
        """Append event and return it with sequence number filled in."""
        async with self._lock:
            cursor = await self._db.execute(
                "INSERT INTO events (id, type, payload, timestamp) VALUES (?, ?, ?, ?)",
                (
                    event.id,
                    event.type.value,
                    json.dumps(event.payload),
                    event.timestamp.isoformat(),
                ),
            )
            await self._db.commit()
            seq = cursor.lastrowid

        # Return a new frozen event with sequence set
        import dataclasses
        return dataclasses.replace(event, sequence=seq)

    async def get_since(self, sequence: int = 0, limit: int = 1000) -> list[Event]:
        async with self._db.execute(
            "SELECT * FROM events WHERE sequence > ? ORDER BY sequence ASC LIMIT ?",
            (sequence, limit),
        ) as cursor:
            rows = await cursor.fetchall()
        return [Event.from_row(dict(r)) for r in rows]

    async def get_by_type(self, event_type: EventType, limit: int = 100) -> list[Event]:
        async with self._db.execute(
            "SELECT * FROM events WHERE type = ? ORDER BY sequence DESC LIMIT ?",
            (event_type.value, limit),
        ) as cursor:
            rows = await cursor.fetchall()
        return [Event.from_row(dict(r)) for r in rows]

    async def get_latest(self, limit: int = 50) -> list[Event]:
        async with self._db.execute(
            "SELECT * FROM events ORDER BY sequence DESC LIMIT ?",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [Event.from_row(dict(r)) for r in reversed(rows)]

    async def count(self) -> int:
        async with self._db.execute("SELECT COUNT(*) FROM events") as cursor:
            row = await cursor.fetchone()
        return row[0]

    async def close(self) -> None:
        if self._db:
            await self._db.close()
