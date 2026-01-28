from __future__ import annotations

from datetime import datetime

from src.core.models.candle import Candle
from src.features.trend.trend_detector import TrendDetector


def create_test_candles(last_close: float) -> list[Candle]:
    return [
        Candle(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            open=last_close,
            high=last_close * 1.01,
            low=last_close * 0.99,
            close=last_close,
            volume=1000.0,
        )
    ]


def test_strong_bullish_returns_bullish_and_strength_positive() -> None:
    candles = create_test_candles(210.0)
    indicators = {
        "sma_50": 205.0,
        "sma_200": 200.0,
        "sma50_slope_pct": 0.01,
        "sma200_slope_pct": 0.005,
    }

    result = TrendDetector.detect(candles, indicators)

    assert result["trend_direction"] == "BULLISH"
    assert isinstance(result["trend_strength"], float)
    assert 0.0 < result["trend_strength"] <= 100.0


def test_strong_bearish_returns_bearish_and_strength_positive() -> None:
    candles = create_test_candles(190.0)
    indicators = {
        "sma_50": 195.0,
        "sma_200": 200.0,
        "sma50_slope_pct": -0.01,
        "sma200_slope_pct": -0.005,
    }

    result = TrendDetector.detect(candles, indicators)

    assert result["trend_direction"] == "BEARISH"
    assert isinstance(result["trend_strength"], float)
    assert 0.0 < result["trend_strength"] <= 100.0


def test_mixed_returns_neutral_and_strength_capped() -> None:
    candles = create_test_candles(210.0)
    indicators = {
        "sma_50": 195.0,
        "sma_200": 200.0,
        "sma50_slope_pct": 0.5,
        "sma200_slope_pct": 0.5,
    }

    result = TrendDetector.detect(candles, indicators)

    assert result["trend_direction"] == "NEUTRAL"
    assert isinstance(result["trend_strength"], float)
    assert 0.0 <= result["trend_strength"] <= 40.0


def test_missing_indicators_returns_neutral_and_zero() -> None:
    candles = create_test_candles(210.0)
    indicators: dict[str, float] = {}

    result = TrendDetector.detect(candles, indicators)

    assert result["trend_direction"] == "NEUTRAL"
    assert result["trend_strength"] == 0.0
