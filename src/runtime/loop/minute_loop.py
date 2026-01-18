from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.models.timeframe import Timeframe
from src.core.ports.clock import Clock
from src.core.ports.orchestrator import OrchestratorProtocol
from src.core.services.scheduler import Scheduler
from src.runtime.config import RuntimeConfig

if TYPE_CHECKING:
    pass


class MinuteLoop:
    def __init__(
        self,
        orchestrator: OrchestratorProtocol,
        scheduler: Scheduler,
        clock: Clock,
        config: RuntimeConfig | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.scheduler = scheduler
        self.clock = clock
        self.config = config or RuntimeConfig()

    def start(
        self,
        symbol: str | None = None,
        timeframe: Timeframe | None = None,
        interval_seconds: float = 60.0,
        max_iterations: int | None = None,
    ) -> None:
        if timeframe is None:
            timeframe = Timeframe(self.config.mvp_timeframe)
        symbols = self.config.mvp_symbols if symbol is None else [symbol]

        iteration_count = 0

        try:
            while True:
                if max_iterations is not None and iteration_count >= max_iterations:
                    break

                current_time = self.clock.now()
                for sym in symbols:
                    if self.scheduler.should_run(sym, timeframe):
                        self.orchestrator.run_analysis(sym, timeframe)

                iteration_count += 1

                if max_iterations is not None and iteration_count >= max_iterations:
                    break

                next_tick = current_time.replace(second=0, microsecond=0)
                next_tick = next_tick.replace(minute=next_tick.minute + 1)
                sleep_seconds = (next_tick - current_time).total_seconds()
                if sleep_seconds <= 0:
                    sleep_seconds = interval_seconds
                if sleep_seconds > 0:
                    self.clock.sleep(sleep_seconds)

        except KeyboardInterrupt:
            pass
