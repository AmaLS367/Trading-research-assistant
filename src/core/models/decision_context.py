from datetime import datetime

from pydantic import BaseModel

from src.core.models.timeframe import Timeframe


class DecisionContext(BaseModel):
    symbol: str
    timestamp: datetime
    timeframe: Timeframe
    market_price: float
    volatility_mode: str
    market_regime: str
    technical_indicators: dict[str, float]
    news_context: str | None = None
