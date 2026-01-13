from src.core.models.timeframe import Timeframe
from src.core.ports.clock import Clock


class Scheduler:
    def __init__(self, clock: Clock) -> None:
        self.clock = clock

    def should_run(self, symbol: str, timeframe: Timeframe) -> bool:
        return True
