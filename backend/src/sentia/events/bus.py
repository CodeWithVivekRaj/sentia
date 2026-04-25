"""Reactive event bus using RxPY - pure functional, no shared mutable state."""
import asyncio
from typing import Callable, Awaitable
from collections import defaultdict
from .types import Event, EventType
from .store import EventStore


Handler = Callable[[Event], Awaitable[None]]


class EventBus:
    """
    Publish-subscribe bus. Publishers emit events; subscribers react.
    All handlers are async. The bus also persists every event to the store.
    """

    def __init__(self, store: EventStore):
        self._store = store
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._wildcard_handlers: list[Handler] = []
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running = False
        self._task: asyncio.Task | None = None

    def subscribe(self, event_type: EventType | None, handler: Handler) -> None:
        """Subscribe to a specific event type or None for all events."""
        if event_type is None:
            self._wildcard_handlers.append(handler)
        else:
            self._handlers[event_type.value].append(handler)

    def unsubscribe(self, event_type: EventType | None, handler: Handler) -> None:
        if event_type is None:
            self._wildcard_handlers = [h for h in self._wildcard_handlers if h is not handler]
        else:
            key = event_type.value
            self._handlers[key] = [h for h in self._handlers[key] if h is not handler]

    async def emit(self, event: Event) -> Event:
        """Persist event to store, then queue for async dispatch."""
        persisted = await self._store.append(event)
        await self._queue.put(persisted)
        return persisted

    async def _dispatch_loop(self) -> None:
        self._running = True
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            await self._dispatch(event)
            self._queue.task_done()

    async def _dispatch(self, event: Event) -> None:
        handlers = self._handlers.get(event.type.value, []) + self._wildcard_handlers
        for handler in handlers:
            try:
                await handler(event)
            except Exception as exc:
                print(f"[EventBus] Handler error for {event.type}: {exc}")

    async def start(self) -> None:
        self._task = asyncio.create_task(self._dispatch_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
