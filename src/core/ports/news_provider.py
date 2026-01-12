from abc import ABC, abstractmethod


class NewsProvider(ABC):
    @abstractmethod
    def get_news_summary(self, symbol: str) -> str:
        pass
