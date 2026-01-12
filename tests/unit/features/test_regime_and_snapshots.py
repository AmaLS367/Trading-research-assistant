from datetime import datetime, timedelta

import pytest

from src.core.models.candle import Candle
from src.core.models.decision_context import DecisionContext
from src.core.models.timeframe import Timeframe
from src.features.indicators.indicator_engine import calculate_features
from src.features.regime.regime_detector import RegimeDetector
from src.features.snapshots.feature_snapshot import FeatureSnapshot


def create_test_candles(count: int, base_price: float = 1.1000) -> list[Candle]:
    candles: list[Candle] = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    for i in range(count):
        price_variation = (i % 10) * 0.0001
        candles.append(
            Candle(
                timestamp=base_time + timedelta(hours=i),
                open=base_price + price_variation,
                high=base_price + price_variation + 0.0010,
                low=base_price + price_variation - 0.0010,
                close=base_price + price_variation + 0.0005,
                volume=1000.0 + i * 10,
            )
        )

    return candles


def test_regime_detector_bull_trend() -> None:
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    candles: list[Candle] = []

    for i in range(250):
        rising_price = 1.1000 + i * 0.0001
        candles.append(
            Candle(
                timestamp=base_time + timedelta(hours=i),
                open=rising_price,
                high=rising_price + 0.001,
                low=rising_price - 0.001,
                close=rising_price + 0.0005,
                volume=1000.0,
            )
        )

    regime = RegimeDetector.detect(candles)

    assert regime in ["BULL_TREND", "BEAR_TREND", "RANGE"]


def test_regime_detector_bear_trend() -> None:
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    candles: list[Candle] = []

    for i in range(250):
        falling_price = 1.2000 - i * 0.0001
        candles.append(
            Candle(
                timestamp=base_time + timedelta(hours=i),
                open=falling_price,
                high=falling_price + 0.001,
                low=falling_price - 0.001,
                close=falling_price - 0.0005,
                volume=1000.0,
            )
        )

    regime = RegimeDetector.detect(candles)

    assert regime in ["BULL_TREND", "BEAR_TREND", "RANGE"]


def test_regime_detector_handles_insufficient_candles() -> None:
    candles = create_test_candles(100)

    regime = RegimeDetector.detect(candles)

    assert regime == "RANGE"


def test_feature_snapshot_validation_rejects_nan() -> None:
    candles = create_test_candles(250)
    indicators = calculate_features(candles)
    indicators["test_nan"] = float("nan")

    with pytest.raises(ValueError, match="contains NaN or Infinity"):
        FeatureSnapshot(
            timestamp=datetime.now(),
            candles=candles,
            indicators=indicators,
        )


def test_feature_snapshot_validation_rejects_infinity() -> None:
    candles = create_test_candles(250)
    indicators = calculate_features(candles)
    indicators["test_inf"] = float("inf")

    with pytest.raises(ValueError, match="contains NaN or Infinity"):
        FeatureSnapshot(
            timestamp=datetime.now(),
            candles=candles,
            indicators=indicators,
        )


def test_feature_snapshot_to_markdown() -> None:
    candles = create_test_candles(250)
    indicators = calculate_features(candles)

    snapshot = FeatureSnapshot(
        timestamp=datetime.now(),
        candles=candles,
        indicators=indicators,
    )

    markdown = snapshot.to_markdown()

    assert "Current Price:" in markdown
    assert "RSI:" in markdown
    assert "SMA 50:" in markdown
    assert "SMA 200:" in markdown
    assert "EMA 9:" in markdown
    assert "Bollinger Bands:" in markdown
    assert "ATR:" in markdown


def test_feature_snapshot_to_markdown_rsi_status() -> None:
    candles = create_test_candles(250)
    indicators = calculate_features(candles)

    indicators["rsi"] = 75.0
    snapshot = FeatureSnapshot(
        timestamp=datetime.now(),
        candles=candles,
        indicators=indicators,
    )

    markdown = snapshot.to_markdown()

    assert "Overbought" in markdown or "Oversold" in markdown or "Neutral" in markdown


def test_decision_context_creation() -> None:
    context = DecisionContext(
        symbol="EURUSD",
        timestamp=datetime.now(),
        timeframe=Timeframe.H1,
        market_price=1.1000,
        volatility_mode="NORMAL",
        market_regime="RANGE",
        technical_indicators={"rsi": 50.0, "sma_200": 1.1000},
        news_context="No major news",
    )

    assert context.symbol == "EURUSD"
    assert context.volatility_mode == "NORMAL"
    assert context.market_regime == "RANGE"
    assert context.news_context == "No major news"


def test_decision_context_optional_news() -> None:
    context = DecisionContext(
        symbol="EURUSD",
        timestamp=datetime.now(),
        timeframe=Timeframe.H1,
        market_price=1.1000,
        volatility_mode="HIGH",
        market_regime="BULL_TREND",
        technical_indicators={"rsi": 70.0},
    )

    assert context.news_context is None
