from typing import Protocol

from src.core.models.timeframe import Timeframe


class OrchestratorProtocol(Protocol):
    def run_analysis(self, symbol: str, timeframe: Timeframe) -> int: ...
