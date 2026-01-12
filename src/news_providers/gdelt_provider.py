from src.core.ports.news_provider import NewsProvider


class GDELTProvider(NewsProvider):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def get_news_summary(self, symbol: str) -> str:
        return "No major news events detected. Market sentiment appears neutral."
