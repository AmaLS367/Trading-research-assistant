from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.core.models.timeframe import Timeframe


class NewsArticle(BaseModel):
    title: str
    url: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[datetime] = None
    language: Optional[str] = None
    relevance_score: float
    query_tag: str


class NewsDigest(BaseModel):
    symbol: str
    timeframe: Timeframe
    window_hours: int
    articles: list[NewsArticle]
    quality: str
    quality_reason: str
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    impact_score: Optional[float] = None
    candidates_total: int = 0
    articles_after_filter: int = 0
    dropped_examples: list[str] = []
    dropped_reason_hint: Optional[str] = None