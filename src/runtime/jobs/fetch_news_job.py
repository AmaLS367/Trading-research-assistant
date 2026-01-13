from src.core.models.news import NewsDigest
from src.core.models.timeframe import Timeframe
from src.core.ports.news_provider import NewsProvider
from src.runtime.jobs.job_result import JobResult


class FetchNewsJob:
    def __init__(self, news_provider: NewsProvider) -> None:
        self.news_provider = news_provider

    def run(self, symbol: str, timeframe: Timeframe) -> JobResult[NewsDigest]:
        try:
            digest = self.news_provider.get_news_digest(symbol=symbol, timeframe=timeframe)
            return JobResult(ok=True, value=digest, error="")

        except Exception as e:
            low_quality_digest = NewsDigest(
                symbol=symbol,
                timeframe=timeframe,
                window_hours=24,
                articles=[],
                quality="LOW",
                quality_reason=f"Provider error: {str(e)}",
            )
            return JobResult(ok=True, value=low_quality_digest, error="")
