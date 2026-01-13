from src.app.settings import settings
from src.core.models.timeframe import Timeframe
from src.core.ports.clock import Clock
from src.core.services.orchestrator import Orchestrator
from src.core.services.scheduler import Scheduler


class MinuteLoop:
    def __init__(
        self,
        orchestrator: Orchestrator,
        scheduler: Scheduler,
        clock: Clock,
    ) -> None:
        self.orchestrator = orchestrator
        self.scheduler = scheduler
        self.clock = clock

    def start(self) -> None:
        timeframe = Timeframe(settings.runtime_mvp_timeframe)
        symbols = settings.mvp_symbols()

        try:
            while True:
                current_time = self.clock.now()
                for symbol in symbols:
                    if self.scheduler.should_run(symbol, timeframe):
                        self.orchestrator.run_analysis(symbol, timeframe)

                next_minute = current_time.replace(second=0, microsecond=0)
                next_minute = next_minute.replace(minute=next_minute.minute + 1)
                sleep_seconds = (next_minute - current_time).total_seconds()
                if sleep_seconds > 0:
                    self.clock.sleep(sleep_seconds)

        except KeyboardInterrupt:
            pass
