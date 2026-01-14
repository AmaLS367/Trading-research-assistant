from datetime import datetime

from pydantic import BaseModel


class Outcome(BaseModel):
    id: int | None = None
    journal_entry_id: int
    close_time: datetime
    win_or_loss: str
    comment: str | None = None
