from enum import Enum

from pydantic import BaseModel


class RationaleType(str, Enum):
    TECHNICAL = "TECHNICAL"
    NEWS = "NEWS"
    SYNTHESIS = "SYNTHESIS"


class Rationale(BaseModel):
    id: int | None = None
    run_id: int
    rationale_type: RationaleType
    content: str
    raw_data: str | None = None
