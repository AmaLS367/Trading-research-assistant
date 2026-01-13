from datetime import datetime

from pydantic import BaseModel

from src.core.models.timeframe import Timeframe


class Recommendation(BaseModel):
    id: int | None = None
    run_id: int | None = None
    symbol: str
    timestamp: datetime
    timeframe: Timeframe
    action: str
    brief: str
    confidence: float
