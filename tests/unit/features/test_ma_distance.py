from __future__ import annotations

import pytest

from src.features.derived.ma_distance import calculate_ma_distances


def test_computes_correct_distances() -> None:
    close_price = 110.0
    indicators = {
        "sma_50": 100.0,
        "sma_200": 200.0,
        "ema_9": 110.0,
    }

    result = calculate_ma_distances(close_price, indicators)

    assert set(result.keys()) == {"dist_sma50_pct", "dist_sma200_pct", "dist_ema9_pct"}
    assert all(isinstance(value, float) for value in result.values())

    assert result["dist_sma50_pct"] == pytest.approx(10.0)
    assert result["dist_sma200_pct"] == pytest.approx(-45.0)
    assert result["dist_ema9_pct"] == pytest.approx(0.0)


def test_missing_ma_keys_return_zero() -> None:
    close_price = 110.0
    indicators: dict[str, float] = {}

    result = calculate_ma_distances(close_price, indicators)

    assert result == {
        "dist_sma50_pct": 0.0,
        "dist_sma200_pct": 0.0,
        "dist_ema9_pct": 0.0,
    }


def test_zero_ma_value_returns_zero_and_does_not_crash() -> None:
    close_price = 110.0
    indicators = {
        "sma_50": 0.0,
        "sma_200": 0.0,
        "ema_9": 0.0,
    }

    result = calculate_ma_distances(close_price, indicators)

    assert result == {
        "dist_sma50_pct": 0.0,
        "dist_sma200_pct": 0.0,
        "dist_ema9_pct": 0.0,
    }
