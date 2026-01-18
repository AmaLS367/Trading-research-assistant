from src.core.models.news import NewsDigest
from src.core.models.timeframe import Timeframe
from src.core.ports.news_provider import NewsProvider
from src.runtime.jobs.job_result import JobResult
from src.utils.logging import get_logger


class FetchNewsJob:
    def __init__(self, news_provider: NewsProvider) -> None:
        self.news_provider = news_provider
        self.logger = get_logger(__name__)

    def run(self, symbol: str, timeframe: Timeframe) -> JobResult[NewsDigest]:
        provider_name = self.news_provider.__class__.__name__
        try:
            digest = self.news_provider.get_news_digest(symbol=symbol, timeframe=timeframe)
            return JobResult[NewsDigest](ok=True, value=digest, error="")

        except Exception as e:
            error_message = (
                f"News provider error: provider={provider_name}, "
                f"symbol={symbol}, timeframe={timeframe.value}, error={e}"
            )
            self.logger.warning(
                error_message,
                exc_info=True,
            )

            low_quality_digest = NewsDigest(
                symbol=symbol,
                timeframe=timeframe,
                window_hours=24,
                articles=[],
                quality="LOW",
                quality_reason=f"Provider error: {str(e)}",
            )
            # ok=True because we have a fallback digest, but error captures what happened
            return JobResult[NewsDigest](ok=True, value=low_quality_digest, error=error_message)
