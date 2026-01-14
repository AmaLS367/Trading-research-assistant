from datetime import datetime
from typing import Any

from pydantic import BaseModel

from src.core.models.timeframe import Timeframe


class NewsArticle(BaseModel):
    title: str
    url: str | None = None
    source: str | None = None
    published_at: datetime | None = None
    language: str | None = None
    relevance_score: float
    query_tag: str


class NewsDigest(BaseModel):
    symbol: str
    timeframe: Timeframe
    window_hours: int
    articles: list[NewsArticle]
    quality: str
    quality_reason: str
    summary: str | None = None
    sentiment: str | None = None
    impact_score: float | None = None
    candidates_total: int = 0
    articles_after_filter: int = 0
    dropped_examples: list[str] = []
    dropped_reason_hint: str | None = None
    pass_counts: dict[str, dict[str, int]] = {}
    queries_used: dict[str, str] = {}
    provider_used: str | None = None
    primary_quality: str | None = None
    primary_reason: str | None = None
    secondary_quality: str | None = None
    secondary_reason: str | None = None
    gdelt_debug: dict[str, Any] = {}
