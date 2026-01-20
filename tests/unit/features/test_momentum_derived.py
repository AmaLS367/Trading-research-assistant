from __future__ import annotations

import math
from datetime import datetime, timedelta

from src.core.models.candle import Candle
from src.features.derived.momentum_derived import calculate_momentum_features


def create_test_candles(closes: list[float]) -> list[Candle]:
    candles: list[Candle] = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    for idx, close in enumerate(closes):
        candles.append(
            Candle(
                timestamp=base_time + timedelta(hours=idx),
                open=close,
                high=close * 1.001,
                low=close * 0.999,
                close=close,
                volume=1000.0,
            )
        )

    return candles


def test_keys_exist_and_values_are_floats_and_not_nan() -> None:
    candles = create_test_candles([100.0 + float(i) for i in range(30)])

    result = calculate_momentum_features(candles)

    assert set(result.keys()) == {"rsi_delta_1", "rsi_delta_5", "roc_5", "roc_20"}
    assert all(isinstance(value, float) for value in result.values())
    assert all(not math.isnan(value) for value in result.values())
    assert all(not math.isinf(value) for value in result.values())


def test_short_series_returns_all_zero_and_no_crash() -> None:
    candles = create_test_candles([100.0 + float(i) for i in range(20)])

    result = calculate_momentum_features(candles)

    assert result == {
        "rsi_delta_1": 0.0,
        "rsi_delta_5": 0.0,
        "roc_5": 0.0,
        "roc_20": 0.0,
    }


def test_upward_series_has_positive_roc_values() -> None:
    candles = create_test_candles([100.0 + float(i) for i in range(40)])

    result = calculate_momentum_features(candles)

    assert result["roc_5"] > 0.0
    assert result["roc_20"] > 0.0
