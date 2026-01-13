from src.core.models.news import NewsDigest
from src.core.models.timeframe import Timeframe
from src.core.ports.news_provider import NewsProvider


class MultiNewsProvider(NewsProvider):
    def __init__(self, primary: NewsProvider, secondary: NewsProvider | None = None) -> None:
        self.primary = primary
        self.secondary = secondary

    def get_news_digest(self, symbol: str, timeframe: Timeframe) -> NewsDigest:
        primary_digest = self.primary.get_news_digest(symbol, timeframe)

        if primary_digest.quality in ("HIGH", "MEDIUM") and primary_digest.articles_after_filter >= 2:
            primary_digest.provider_used = "GDELT"
            primary_digest.primary_quality = primary_digest.quality
            primary_digest.primary_reason = primary_digest.quality_reason
            return primary_digest

        if self.secondary is not None:
            secondary_digest = self.secondary.get_news_digest(symbol, timeframe)

            if secondary_digest.quality in ("HIGH", "MEDIUM"):
                secondary_digest.provider_used = "NEWSAPI"
                secondary_digest.primary_quality = primary_digest.quality
                secondary_digest.primary_reason = primary_digest.quality_reason
                secondary_digest.secondary_quality = secondary_digest.quality
                secondary_digest.secondary_reason = secondary_digest.quality_reason
                return secondary_digest
            else:
                primary_digest.provider_used = "NONE"
                primary_digest.primary_quality = primary_digest.quality
                primary_digest.primary_reason = primary_digest.quality_reason
                primary_digest.secondary_quality = secondary_digest.quality
                primary_digest.secondary_reason = secondary_digest.quality_reason
                combined_reason = f"GDELT LOW ({primary_digest.primary_reason}) + NewsAPI LOW ({secondary_digest.quality_reason})"
                primary_digest.quality_reason = combined_reason
                return primary_digest
        else:
            primary_digest.provider_used = "GDELT"
            primary_digest.primary_quality = primary_digest.quality
            primary_digest.primary_reason = primary_digest.quality_reason
            if primary_digest.quality_reason:
                primary_digest.quality_reason = f"{primary_digest.quality_reason} NewsAPI disabled (no API key)"
            else:
                primary_digest.quality_reason = "NewsAPI disabled (no API key)"
            return primary_digest

    def get_news_summary(self, symbol: str) -> str:
        digest = self.get_news_digest(symbol, Timeframe.H1)
        if digest.summary:
            return digest.summary
        return "No news found."
