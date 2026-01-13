from enum import Enum
from typing import Optional

from pydantic import BaseModel


class RationaleType(str, Enum):
    TECHNICAL = "TECHNICAL"
    NEWS = "NEWS"
    SYNTHESIS = "SYNTHESIS"


class Rationale(BaseModel):
    id: Optional[int] = None
    run_id: int
    rationale_type: RationaleType
    content: str
    raw_data: Optional[str] = None