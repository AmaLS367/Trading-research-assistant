from abc import ABC, abstractmethod
from datetime import datetime

from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe


class MarketDataProvider(ABC):
    @abstractmethod
    def fetch_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> list[Candle]:
        pass
