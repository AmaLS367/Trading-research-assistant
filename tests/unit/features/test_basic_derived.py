from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.core.models.candle import Candle
from src.features.derived.basic_derived import calculate_basic_derived


def create_test_candles(
    closes: list[float],
    *,
    start_time: datetime | None = None,
) -> list[Candle]:
    candles: list[Candle] = []
    base_time = start_time or datetime(2024, 1, 1, 12, 0, 0)

    for idx, close in enumerate(closes):
        candles.append(
            Candle(
                timestamp=base_time + timedelta(hours=idx),
                open=close,
                high=close * 1.01,
                low=close * 0.99,
                close=close,
                volume=1000.0,
            )
        )

    return candles


def test_derived_keys_exist_and_are_floats() -> None:
    candles = create_test_candles([100.0 + float(i) for i in range(25)])

    derived = calculate_basic_derived(candles)

    assert set(derived.keys()) == {
        "price_change_pct_1",
        "price_change_pct_5",
        "price_change_pct_20",
        "range_pct",
        "body_pct",
    }
    assert all(isinstance(value, float) for value in derived.values())


def test_nan_safety_shift_20_becomes_zero() -> None:
    candles = create_test_candles([100.0 + float(i) for i in range(5)])

    derived = calculate_basic_derived(candles)

    assert derived["price_change_pct_20"] == 0.0


def test_price_change_pct_1_sanity() -> None:
    candles = create_test_candles([100.0, 110.0])

    derived = calculate_basic_derived(candles)

    assert derived["price_change_pct_1"] == pytest.approx(10.0)
