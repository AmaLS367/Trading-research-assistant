from datetime import datetime, timedelta
from unittest.mock import Mock

from src.core.models.timeframe import Timeframe
from src.core.ports.clock import Clock
from src.core.ports.orchestrator import OrchestratorProtocol
from src.core.services.scheduler import Scheduler
from src.runtime.loop.minute_loop import MinuteLoop


class MockClock(Clock):
    def __init__(self) -> None:
        self.current_time = datetime(2024, 1, 1, 12, 0, 0)
        self.sleep_calls: list[float] = []

    def now(self) -> datetime:
        return self.current_time

    def sleep(self, seconds: float) -> None:
        self.sleep_calls.append(seconds)
        self.current_time += timedelta(seconds=seconds)


def test_minute_loop_runs_n_iterations() -> None:
    mock_orchestrator = Mock(spec=OrchestratorProtocol)
    mock_orchestrator.run_analysis.return_value = 1

    mock_clock = MockClock()
    scheduler = Scheduler(mock_clock)
    loop = MinuteLoop(orchestrator=mock_orchestrator, scheduler=scheduler, clock=mock_clock)

    loop.start(symbol="EURUSD", timeframe=Timeframe.H1, max_iterations=3, interval_seconds=0.1)

    assert mock_orchestrator.run_analysis.call_count == 3
    assert len(mock_clock.sleep_calls) == 2
