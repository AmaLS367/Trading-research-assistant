from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.core.models.candle import Candle
from src.features.derived.ma_slope import calculate_ma_slopes


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


def test_upward_series_slopes_are_positive() -> None:
    candles = create_test_candles([100.0 + float(i) for i in range(220)])

    result = calculate_ma_slopes(candles, slope_window=10)

    assert set(result.keys()) == {"sma50_slope_pct", "sma200_slope_pct", "ema9_slope_pct"}
    assert all(isinstance(value, float) for value in result.values())

    assert result["sma50_slope_pct"] > 0.0
    assert result["sma200_slope_pct"] > 0.0
    assert result["ema9_slope_pct"] > 0.0


def test_constant_series_slopes_are_near_zero() -> None:
    candles = create_test_candles([100.0 for _ in range(220)])

    result = calculate_ma_slopes(candles, slope_window=10)

    assert result["sma50_slope_pct"] == pytest.approx(0.0, abs=1e-8)
    assert result["sma200_slope_pct"] == pytest.approx(0.0, abs=1e-8)
    assert result["ema9_slope_pct"] == pytest.approx(0.0, abs=1e-8)


def test_short_series_sma200_slope_is_zero_and_no_crash() -> None:
    candles = create_test_candles([100.0 + float(i) for i in range(50)])

    result = calculate_ma_slopes(candles, slope_window=10)

    assert set(result.keys()) == {"sma50_slope_pct", "sma200_slope_pct", "ema9_slope_pct"}
    assert all(isinstance(value, float) for value in result.values())
    assert result["sma200_slope_pct"] == 0.0
