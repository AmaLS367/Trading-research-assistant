from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from src.core.models.timeframe import Timeframe


class Recommendation(BaseModel):
    id: Optional[int] = None
    symbol: str
    timestamp: datetime
    timeframe: Timeframe
    brief: str
    confidence: float
