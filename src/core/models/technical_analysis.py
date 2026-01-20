from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TechnicalAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    bias: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    setup_type: str | None = None
    no_trade_flags: list[str] = Field(default_factory=list)
