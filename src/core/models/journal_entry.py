from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class JournalEntry(BaseModel):
    id: Optional[int] = None
    recommendation_id: int
    symbol: str
    open_time: datetime
    expiry_seconds: int
    user_action: str
