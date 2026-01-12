from datetime import datetime, timedelta
from unittest.mock import Mock

import httpx
import pytest

from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe
from src.data_providers.forex.fallback_provider import FallbackMarketDataProvider
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
    technical_analyst.analyze.return_value = "Technical view: bullish"

    synthesizer = Mock()
    from src.core.models.recommendation import Recommendation

    synthesizer.synthesize.return_value = Recommendation(
        symbol="EURUSD",
        timestamp=datetime.now(),
        timeframe=Timeframe.H1,
        action="CALL",
        brief="Test recommendation",
        confidence=0.7,
    )

    recommendations_repo = Mock()
    recommendations_repo.save.return_value = 1

    job = RunAgentsJob(
        market_data_provider=fallback_provider,
        news_provider=news_provider,
        technical_analyst=technical_analyst,
        synthesizer=synthesizer,
        recommendations_repository=recommendations_repo,
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
    news_provider.get_news_summary.return_value = "No news"

    technical_analyst = Mock()
    technical_analyst.analyze.return_value = "Technical view: bullish"

    synthesizer = Mock()
    from src.core.models.recommendation import Recommendation

    synthesizer.synthesize.return_value = Recommendation(
        symbol="EURUSD",
        timestamp=datetime.now(),
        timeframe=Timeframe.H1,
        action="CALL",
        brief="Test recommendation",
        confidence=0.7,
    )

    recommendations_repo = Mock()
    recommendations_repo.save.return_value = 1

    job = RunAgentsJob(
        market_data_provider=fallback_provider,
        news_provider=news_provider,
        technical_analyst=technical_analyst,
        synthesizer=synthesizer,
        recommendations_repository=recommendations_repo,
    )

    recommendation_id = job.run(symbol="EURUSD", timeframe=Timeframe.H1, count=200)

    assert recommendation_id == 1
    primary.fetch_candles.assert_called_once()
    secondary.fetch_candles.assert_not_called()
    technical_analyst.analyze.assert_called_once()
    synthesizer.synthesize.assert_called_once()
    recommendations_repo.save.assert_called_once()
