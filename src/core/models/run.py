from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from src.core.models.timeframe import Timeframe


class RunStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Run(BaseModel):
    id: int | None = None
    symbol: str
    timeframe: Timeframe
    start_time: datetime
    end_time: datetime | None = None
    status: RunStatus
    error_message: str | None = None
