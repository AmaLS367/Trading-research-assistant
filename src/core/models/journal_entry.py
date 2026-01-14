from datetime import datetime

from pydantic import BaseModel


class JournalEntry(BaseModel):
    id: int | None = None
    recommendation_id: int
    symbol: str
    open_time: datetime
    expiry_seconds: int
    user_action: str
