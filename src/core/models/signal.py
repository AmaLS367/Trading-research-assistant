from datetime import datetime

from pydantic import BaseModel

from src.core.models.timeframe import Timeframe


class Signal(BaseModel):
    symbol: str
    timeframe: Timeframe
    timestamp: datetime
    indicators: dict[str, float]
    regime: str
    volatility: str
