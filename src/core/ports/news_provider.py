from abc import ABC, abstractmethod

from src.core.models.news import NewsDigest
from src.core.models.timeframe import Timeframe


class NewsProvider(ABC):
    @abstractmethod
    def get_news_summary(self, symbol: str) -> str:
        pass

    @abstractmethod
    def get_news_digest(self, symbol: str, timeframe: Timeframe) -> NewsDigest:
        pass
