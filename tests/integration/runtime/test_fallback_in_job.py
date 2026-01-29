from datetime import datetime, timedelta
from unittest.mock import Mock

import httpx
import pytest

from src.core.models.candle import Candle
from src.core.models.news import NewsDigest
from src.core.models.timeframe import Timeframe
from src.data_providers.forex.fallback_provider import FallbackMarketDataProvider
from src.runtime.jobs.build_features_job import BuildFeaturesJob
from src.runtime.jobs.run_agents_job import RunAgentsJob


def test_job_continues_with_fallback_when_primary_fails() -> None:
    primary = Mock()
    secondary = Mock()

    primary.fetch_candles.side_effect = httpx.NetworkError("Primary failed")

    base_time = datetime(2024, 1, 1, 12, 0, 0)
    test_candles = [
        Candle(
            timestamp=base_time + timedelta(hours=i),
            open=1.0 + i * 0.001,
            high=1.1 + i * 0.001,
            low=0.9 + i * 0.001,
            close=1.05 + i * 0.001,
            volume=1000.0,
        )
        for i in range(200)
    ]

    secondary.fetch_candles.return_value = test_candles

    fallback_provider = FallbackMarketDataProvider(primary=primary, secondary=secondary)

    news_provider = Mock()
    news_provider.get_news_summary.return_value = "No news"

    technical_analyst = Mock()
    from src.core.models.llm import LlmResponse

    technical_analyst.analyze.return_value = (
        "Technical view: bullish",
        LlmResponse(
            text="Technical view: bullish",
            provider_name="test",
            model_name="test",
            latency_ms=100,
            attempts=1,
            error=None,
        ),
    )

    synthesizer = Mock()
    from src.core.models.recommendation import Recommendation

    synthesizer.synthesize.return_value = (
        Recommendation(
            symbol="EURUSD",
            timestamp=datetime.now(),
            timeframe=Timeframe.H1,
            action="CALL",
            brief="Test recommendation",
            confidence=0.7,
        ),
        {
            "parse_ok": True,
            "parse_error": None,
            "raw_output": "",
            "retry_used": False,
            "retry_raw_output": None,
            "brief_warning": None,
        },
        None,
    )

    recommendations_repo = Mock()
    recommendations_repo.save.return_value = 1

    runs_repo = Mock()
    runs_repo.create.return_value = 1

    rationales_repo = Mock()

    news_analyst = Mock()
    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )
    news_analyst.analyze.return_value = (news_digest, None)
    news_provider.get_news_digest.return_value = news_digest

    job = RunAgentsJob(
        market_data_provider=fallback_provider,
        news_provider=news_provider,
        technical_analyst=technical_analyst,
        synthesizer=synthesizer,
        news_analyst=news_analyst,
        recommendations_repository=recommendations_repo,
        runs_repository=runs_repo,
        rationales_repository=rationales_repo,
        build_features_job=BuildFeaturesJob(),
    )

    with pytest.warns(UserWarning, match="failed.*Falling back"):
        recommendation_id = job.run(symbol="EURUSD", timeframe=Timeframe.H1, count=200)

    assert recommendation_id == 1
    primary.fetch_candles.assert_called_once()
    secondary.fetch_candles.assert_called_once()
    technical_analyst.analyze.assert_called_once()
    synthesizer.synthesize.assert_called_once()
    recommendations_repo.save.assert_called_once()


def test_job_uses_primary_when_successful() -> None:
    primary = Mock()
    secondary = Mock()

    base_time = datetime(2024, 1, 1, 12, 0, 0)
    test_candles = [
        Candle(
            timestamp=base_time + timedelta(hours=i),
            open=1.0 + i * 0.001,
            high=1.1 + i * 0.001,
            low=0.9 + i * 0.001,
            close=1.05 + i * 0.001,
            volume=1000.0,
        )
        for i in range(200)
    ]

    primary.fetch_candles.return_value = test_candles

    fallback_provider = FallbackMarketDataProvider(primary=primary, secondary=secondary)

    news_provider = Mock()
    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )
    news_provider.get_news_digest.return_value = news_digest

    news_analyst = Mock()
    news_analyst.analyze.return_value = (news_digest, None)

    technical_analyst = Mock()
    from src.core.models.llm import LlmResponse

    technical_analyst.analyze.return_value = (
        "Technical view: bullish",
        LlmResponse(
            text="Technical view: bullish",
            provider_name="test",
            model_name="test",
            latency_ms=100,
            attempts=1,
            error=None,
        ),
    )

    synthesizer = Mock()
    from src.core.models.recommendation import Recommendation

    synthesizer.synthesize.return_value = (
        Recommendation(
            symbol="EURUSD",
            timestamp=datetime.now(),
            timeframe=Timeframe.H1,
            action="CALL",
            brief="Test recommendation",
            confidence=0.7,
        ),
        {
            "parse_ok": True,
            "parse_error": None,
            "raw_output": "",
            "retry_used": False,
            "retry_raw_output": None,
            "brief_warning": None,
        },
        None,
    )

    recommendations_repo = Mock()
    recommendations_repo.save.return_value = 1

    runs_repo = Mock()
    runs_repo.create.return_value = 1

    rationales_repo = Mock()

    job = RunAgentsJob(
        market_data_provider=fallback_provider,
        news_provider=news_provider,
        technical_analyst=technical_analyst,
        synthesizer=synthesizer,
        news_analyst=news_analyst,
        recommendations_repository=recommendations_repo,
        runs_repository=runs_repo,
        rationales_repository=rationales_repo,
        build_features_job=BuildFeaturesJob(),
    )

    recommendation_id = job.run(symbol="EURUSD", timeframe=Timeframe.H1, count=200)

    assert recommendation_id == 1
    primary.fetch_candles.assert_called_once()
    secondary.fetch_candles.assert_not_called()
    technical_analyst.analyze.assert_called_once()
    synthesizer.synthesize.assert_called_once()
    recommendations_repo.save.assert_called_once()
