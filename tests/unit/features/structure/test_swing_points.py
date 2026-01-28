from __future__ import annotations

from datetime import datetime, timedelta

from src.core.models.candle import Candle
from src.features.structure.swing_points import detect_swings


def create_candles_from_high_low(highs: list[float], lows: list[float]) -> list[Candle]:
    candles: list[Candle] = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    for idx, (high, low) in enumerate(zip(highs, lows, strict=True)):
        mid = (high + low) / 2.0
        candles.append(
            Candle(
                timestamp=base_time + timedelta(hours=idx),
                open=mid,
                high=high,
                low=low,
                close=mid,
                volume=1000.0,
            )
        )

    return candles


def test_v_shape_returns_one_low_pivot() -> None:
    depth = 2
    lows = [5.0, 4.0, 3.0, 1.0, 3.0, 4.0, 5.0]
    highs = [low + 2.0 for low in lows]
    candles = create_candles_from_high_low(highs, lows)

    swings = detect_swings(candles, depth=depth)

    assert len(swings) == 1
    assert swings[0].type == "LOW"
    assert swings[0].index == 3
    assert swings[0].price == 1.0
    assert swings[0].timestamp == candles[3].timestamp


def test_a_shape_returns_one_high_pivot() -> None:
    depth = 2
    highs = [5.0, 6.0, 7.0, 10.0, 7.0, 6.0, 5.0]
    lows = [1.0, 2.0, 3.0, 4.0, 3.0, 2.0, 1.0]
    candles = create_candles_from_high_low(highs, lows)

    swings = detect_swings(candles, depth=depth)

    assert len(swings) == 1
    assert swings[0].type == "HIGH"
    assert swings[0].index == 3
    assert swings[0].price == 10.0
    assert swings[0].timestamp == candles[3].timestamp


def test_swings_are_sorted_by_index() -> None:
    depth = 2
    lows = [5.0, 4.0, 3.0, 1.0, 3.0, 4.0, 2.0, 4.0, 5.0]
    highs = [7.0, 8.0, 9.0, 6.0, 9.0, 8.0, 10.0, 8.0, 7.0]
    candles = create_candles_from_high_low(highs, lows)

    swings = detect_swings(candles, depth=depth)

    indices = [s.index for s in swings]
    assert indices == sorted(indices)


def test_insufficient_candles_returns_empty() -> None:
    candles = create_candles_from_high_low([2.0, 2.0, 2.0, 2.0], [1.0, 1.0, 1.0, 1.0])

    swings = detect_swings(candles, depth=2)

    assert swings == []
