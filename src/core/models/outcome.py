from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Outcome(BaseModel):
    id: Optional[int] = None
    journal_entry_id: int
    close_time: datetime
    win_or_loss: str
    comment: Optional[str] = None
