"""
Tests for FetchNewsJob failure observability.

Verifies that exceptions are logged and JobResult.error is populated
while still returning ok=True with a degraded LOW quality digest.
"""

from src.core.models.news import NewsDigest
from src.core.models.timeframe import Timeframe
from src.core.ports.news_provider import NewsProvider
from src.runtime.jobs.fetch_news_job import FetchNewsJob


class MockNewsProvider(NewsProvider):
    """Mock news provider that can be configured to fail."""

    def __init__(self, should_fail: bool = False, fail_message: str = "Mock failure") -> None:
        self._should_fail = should_fail
        self._fail_message = fail_message

    def get_news_summary(self, symbol: str) -> str:
        if self._should_fail:
            raise ConnectionError(self._fail_message)
        return f"News summary for {symbol}"

    def get_news_digest(self, symbol: str, timeframe: Timeframe) -> NewsDigest:
        if self._should_fail:
            raise ConnectionError(self._fail_message)
        return NewsDigest(
            symbol=symbol,
            timeframe=timeframe,
            window_hours=24,
            articles=[],
            quality="MEDIUM",
            quality_reason="Mock news",
        )


def test_fetch_news_job_provider_error_returns_ok_true() -> None:
    """Provider error: ok=True so pipeline continues with degraded digest."""
    provider = MockNewsProvider(should_fail=True, fail_message="Network timeout")
    job = FetchNewsJob(provider)

    result = job.run(symbol="EURUSD", timeframe=Timeframe.H1)

    # ok should be True because we have a fallback digest
    assert result.ok is True
    assert result.value is not None
    assert result.value.quality == "LOW"


def test_fetch_news_job_provider_error_populates_error_field() -> None:
    """Provider error: JobResult.error should contain meaningful info."""
    provider = MockNewsProvider(should_fail=True, fail_message="API rate limit exceeded")
    job = FetchNewsJob(provider)

    result = job.run(symbol="GBPUSD", timeframe=Timeframe.M15)

    # error should not be empty
    assert result.error != ""
    assert "API rate limit exceeded" in result.error
    assert "GBPUSD" in result.error
    assert "MockNewsProvider" in result.error


def test_fetch_news_job_provider_error_digest_has_reason() -> None:
    """Provider error: digest.quality_reason should contain error details."""
    provider = MockNewsProvider(should_fail=True, fail_message="Server unreachable")
    job = FetchNewsJob(provider)

    result = job.run(symbol="USDJPY", timeframe=Timeframe.H1)

    assert result.value is not None
    assert "Server unreachable" in result.value.quality_reason


def test_fetch_news_job_provider_error_logs_warning(caplog) -> None:
    """Provider error: should log a warning with context."""
    provider = MockNewsProvider(should_fail=True, fail_message="Connection refused")
    job = FetchNewsJob(provider)

    with caplog.at_level("WARNING"):
        job.run(symbol="EURUSD", timeframe=Timeframe.H1)

    # Check that warning was logged
    warning_logs = [r for r in caplog.records if r.levelname == "WARNING"]
    assert len(warning_logs) > 0

    warning_text = warning_logs[0].getMessage()
    assert "Connection refused" in warning_text or "Connection refused" in str(caplog.text)


def test_fetch_news_job_success_no_error() -> None:
    """Successful fetch: error should be empty string."""
    provider = MockNewsProvider(should_fail=False)
    job = FetchNewsJob(provider)

    result = job.run(symbol="EURUSD", timeframe=Timeframe.H1)

    assert result.ok is True
    assert result.error == ""
    assert result.value is not None
    assert result.value.quality == "MEDIUM"
