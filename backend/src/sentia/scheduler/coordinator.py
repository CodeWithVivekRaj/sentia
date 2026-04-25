"""APScheduler coordinator — wires tick intervals to body engine."""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..body.engine import BodyEngine

log = logging.getLogger("sentia.scheduler")


class TickCoordinator:
    def __init__(self, body_engine: "BodyEngine") -> None:
        self._body = body_engine
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._slow_interval: int = 300

    def setup(
        self,
        fast_interval: int = 30,
        slow_interval: int = 300,
        daily_interval: int = 86400,
    ) -> None:
        self._slow_interval = slow_interval
        self._scheduler.add_job(
            self._fast,
            IntervalTrigger(seconds=fast_interval),
            id="fast_tick",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.add_job(
            self._slow,
            IntervalTrigger(seconds=slow_interval),
            id="slow_tick",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.add_job(
            self._daily,
            IntervalTrigger(seconds=daily_interval),
            id="daily_tick",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        log.info(
            "Ticks configured: fast=%ds  slow=%ds  daily=%ds",
            fast_interval, slow_interval, daily_interval,
        )

    async def _fast(self) -> None:
        try:
            await self._body.fast_tick(dt_seconds=30.0)
        except Exception:
            log.exception("Fast tick error")

    async def _slow(self) -> None:
        try:
            await self._body.slow_tick(dt_seconds=float(self._slow_interval))
        except Exception:
            log.exception("Slow tick error")

    async def _daily(self) -> None:
        try:
            await self._body.daily_tick()
        except Exception:
            log.exception("Daily tick error")

    def start(self) -> None:
        self._scheduler.start()
        log.info("Tick scheduler started")

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        log.info("Tick scheduler stopped")
