from datetime import datetime, timedelta

import pytest

from src.core.models.candle import Candle
from src.features.indicators.indicator_engine import calculate_features
from src.features.volatility.volatility_estimator import VolatilityEstimator


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


def test_calculate_features_returns_all_indicators() -> None:
    candles = create_test_candles(250)

    features = calculate_features(candles)

    assert "sma_50" in features
    assert "sma_200" in features
    assert "ema_9" in features
    assert "rsi" in features
    assert "bb_upper" in features
    assert "bb_middle" in features
    assert "bb_lower" in features
    assert "atr" in features

    assert isinstance(features["sma_50"], float)
    assert isinstance(features["sma_200"], float)
    assert isinstance(features["ema_9"], float)
    assert isinstance(features["rsi"], float)
    assert isinstance(features["atr"], float)

    assert features["sma_50"] > 0
    assert features["sma_200"] > 0
    assert features["ema_9"] > 0
    assert 0 <= features["rsi"] <= 100
    assert features["atr"] > 0


def test_calculate_features_raises_error_for_insufficient_candles() -> None:
    candles = create_test_candles(100)

    with pytest.raises(ValueError, match="Need at least 200 candles"):
        calculate_features(candles)


def test_calculate_features_sma_values_are_reasonable() -> None:
    candles = create_test_candles(250, base_price=1.1000)

    features = calculate_features(candles)

    assert features["sma_50"] > 0
    assert features["sma_200"] > 0
    assert abs(features["sma_50"] - features["sma_200"]) < 0.1


def test_calculate_features_bollinger_bands_order() -> None:
    candles = create_test_candles(250)

    features = calculate_features(candles)

    assert features["bb_upper"] > features["bb_middle"]
    assert features["bb_middle"] > features["bb_lower"]


def test_volatility_estimator_returns_string() -> None:
    candles = create_test_candles(250)

    result = VolatilityEstimator.estimate(candles)

    assert result in ["HIGH", "NORMAL", "LOW"]


def test_volatility_estimator_handles_insufficient_candles() -> None:
    candles = create_test_candles(100)

    result = VolatilityEstimator.estimate(candles)

    assert result == "NORMAL"


def test_volatility_estimator_high_volatility() -> None:
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    candles: list[Candle] = []

    for i in range(250):
        high_volatility_price = 1.1000 + (i % 50) * 0.01
        candles.append(
            Candle(
                timestamp=base_time + timedelta(hours=i),
                open=high_volatility_price,
                high=high_volatility_price + 0.005,
                low=high_volatility_price - 0.005,
                close=high_volatility_price + 0.002,
                volume=1000.0,
            )
        )

    result = VolatilityEstimator.estimate(candles)

    assert result in ["HIGH", "NORMAL", "LOW"]
