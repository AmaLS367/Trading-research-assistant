"""
Tests for RUNTIME_MARKET_DATA_WINDOW_CANDLES configuration.

Verifies that the runtime_market_data_window_candles setting
actually controls the number of candles fetched.
"""

import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe
from src.core.ports.market_data_provider import MarketDataProvider
from src.runtime.jobs.fetch_market_data_job import FetchMarketDataJob


class MockMarketDataProvider(MarketDataProvider):
    """Mock provider that tracks the requested count."""

    def __init__(self) -> None:
        self.last_requested_count: int | None = None

    def fetch_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> list[Candle]:
        self.last_requested_count = count
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        # Return enough candles to pass the minimum check
        return [
            Candle(
                timestamp=base_time + timedelta(minutes=i),
                open=1.1 + i * 0.0001,
                high=1.1 + i * 0.0001 + 0.0005,
                low=1.1 + i * 0.0001 - 0.0003,
                close=1.1 + i * 0.0001 + 0.0002,
                volume=1000.0,
            )
            for i in range(count)
        ]


def test_fetch_market_data_job_uses_provided_count() -> None:
    """FetchMarketDataJob should use the count parameter provided."""
    provider = MockMarketDataProvider()
    job = FetchMarketDataJob(provider)

    result = job.run(symbol="EURUSD", timeframe=Timeframe.H1, count=250)

    assert result.ok
    assert provider.last_requested_count == 250


def test_fetch_market_data_job_custom_count_150() -> None:
    """FetchMarketDataJob should work with count=150 (below default 300)."""
    provider = MockMarketDataProvider()
    job = FetchMarketDataJob(provider)

    # 150 is below minimum 200, should fail
    result = job.run(symbol="EURUSD", timeframe=Timeframe.H1, count=150)

    assert not result.ok
    assert "insufficient" in result.error.lower() or "candles" in result.error.lower()


def test_fetch_market_data_job_default_count() -> None:
    """FetchMarketDataJob default count should be 300."""
    provider = MockMarketDataProvider()
    job = FetchMarketDataJob(provider)

    # Call without specifying count to use default
    result = job.run(symbol="EURUSD", timeframe=Timeframe.H1)

    assert result.ok
    assert provider.last_requested_count == 300


@patch.dict(os.environ, {"RUNTIME_MARKET_DATA_WINDOW_CANDLES": "400"})
def test_settings_parses_market_data_window_candles_from_env() -> None:
    """Settings should parse RUNTIME_MARKET_DATA_WINDOW_CANDLES from environment."""
    # Need to reimport settings to pick up the new env var
    from importlib import reload
    from src.app import settings as settings_module

    # Clear the cached settings
    settings_module.get_settings.cache_clear()

    try:
        reloaded_settings = settings_module.get_settings()
        assert reloaded_settings.runtime_market_data_window_candles == 400
    finally:
        # Reset cache for other tests
        settings_module.get_settings.cache_clear()


def test_orchestrator_uses_settings_candles_count() -> None:
    """RuntimeOrchestrator should use settings.runtime_market_data_window_candles."""
    from unittest.mock import MagicMock, patch

    from src.core.models.run import Run, RunStatus
    from src.runtime.orchestrator import RuntimeOrchestrator

    # Create mock settings with custom candles count
    mock_settings = MagicMock()
    mock_settings.runtime_market_data_window_candles = 250
    mock_settings.runtime_llm_enabled = True
    mock_settings.llm_verifier_enabled = False
    mock_settings.llm_verifier_mode = "soft"
    mock_settings.llm_verifier_max_repairs = 1

    # Mock provider that tracks requested count
    mock_market_provider = MockMarketDataProvider()

    # Mock storage
    mock_storage = MagicMock()
    mock_storage.runs.create.return_value = 1
    mock_storage.runs.update_run.return_value = None

    # Mock artifact store
    mock_artifact_store = MagicMock()

    # Mock other dependencies to fail early (we just want to test candles_count is passed)
    mock_news_provider = MagicMock()
    mock_news_provider.get_news_digest.side_effect = Exception("Stop here")

    mock_tech_analyst = MagicMock()
    mock_news_analyst = MagicMock()
    mock_synthesizer = MagicMock()

    orchestrator = RuntimeOrchestrator(
        storage=mock_storage,
        artifact_store=mock_artifact_store,
        market_data_provider=mock_market_provider,
        news_provider=mock_news_provider,
        technical_analyst=mock_tech_analyst,
        news_analyst=mock_news_analyst,
        synthesizer=mock_synthesizer,
        candles_repository=None,
        verifier_agent=None,
        verification_repository=None,
        verifier_enabled=False,
        trace=None,
    )

    with patch("src.runtime.orchestrator.settings", mock_settings):
        # Run will fail at news fetch, but we can check the candles count was used
        orchestrator.run_analysis(symbol="EURUSD", timeframe=Timeframe.H1)

    assert mock_market_provider.last_requested_count == 250
