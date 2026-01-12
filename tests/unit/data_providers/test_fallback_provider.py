from datetime import datetime
from unittest.mock import Mock

import httpx
import pytest

from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe
from src.data_providers.forex.fallback_provider import FallbackMarketDataProvider


def test_fallback_provider_uses_primary_when_successful() -> None:
    primary = Mock()
    secondary = Mock()

    test_candles = [
        Candle(
            timestamp=datetime.now(),
            open=1.0,
            high=1.1,
            low=0.9,
            close=1.05,
            volume=1000.0,
        )
    ]

    primary.fetch_candles.return_value = test_candles

    fallback = FallbackMarketDataProvider(primary=primary, secondary=secondary)

    result = fallback.fetch_candles(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        count=100,
    )

    assert result == test_candles
    primary.fetch_candles.assert_called_once()
    secondary.fetch_candles.assert_not_called()


def test_fallback_provider_uses_secondary_when_primary_fails() -> None:
    primary = Mock()
    secondary = Mock()

    primary.fetch_candles.side_effect = httpx.NetworkError("Connection failed")

    test_candles = [
        Candle(
            timestamp=datetime.now(),
            open=1.0,
            high=1.1,
            low=0.9,
            close=1.05,
            volume=1000.0,
        )
    ]

    secondary.fetch_candles.return_value = test_candles

    fallback = FallbackMarketDataProvider(primary=primary, secondary=secondary)

    with pytest.warns(UserWarning, match="failed.*Falling back"):
        result = fallback.fetch_candles(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            count=100,
        )

    assert result == test_candles
    primary.fetch_candles.assert_called_once()
    secondary.fetch_candles.assert_called_once()


def test_fallback_provider_raises_when_both_fail() -> None:
    primary = Mock()
    secondary = Mock()

    primary_error = httpx.NetworkError("Primary connection failed")
    secondary_error = httpx.TimeoutException("Secondary timeout")

    primary.fetch_candles.side_effect = primary_error
    secondary.fetch_candles.side_effect = secondary_error

    fallback = FallbackMarketDataProvider(primary=primary, secondary=secondary)

    with pytest.warns(UserWarning):
        with pytest.raises(RuntimeError, match="Both providers failed"):
            fallback.fetch_candles(
                symbol="EURUSD",
                timeframe=Timeframe.H1,
                count=100,
            )

    primary.fetch_candles.assert_called_once()
    secondary.fetch_candles.assert_called_once()


def test_fallback_provider_raises_when_primary_fails_and_no_secondary() -> None:
    primary = Mock()

    primary_error = httpx.NetworkError("Connection failed")
    primary.fetch_candles.side_effect = primary_error

    fallback = FallbackMarketDataProvider(primary=primary, secondary=None)

    with pytest.raises(httpx.NetworkError):
        fallback.fetch_candles(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            count=100,
        )

    primary.fetch_candles.assert_called_once()
