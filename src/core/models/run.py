from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from src.core.models.timeframe import Timeframe


class RunStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Run(BaseModel):
    id: Optional[int] = None
    symbol: str
    timeframe: Timeframe
    start_time: datetime
    end_time: Optional[datetime] = None
    status: RunStatus
    error_message: Optional[str] = None