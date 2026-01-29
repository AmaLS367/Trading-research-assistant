from __future__ import annotations

from datetime import datetime, timedelta

from src.core.models.candle import Candle
from src.features.contracts.feature_contract import FeatureContract, ValidationStatus


def create_test_candles(
    count: int,
    *,
    base_price: float = 1.1000,
    volume: float = 1000.0,
    start_time: datetime | None = None,
    step: timedelta = timedelta(hours=1),
) -> list[Candle]:
    candles: list[Candle] = []
    base_time = start_time or datetime(2024, 1, 1, 12, 0, 0)

    for i in range(count):
        price_variation = (i % 10) * 0.0001
        open_price = base_price + price_variation
        high_price = open_price + 0.0010
        low_price = open_price - 0.0010
        close_price = open_price + 0.0005
        candles.append(
            Candle(
                timestamp=base_time + (step * i),
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )
        )

    return candles


def test_valid_candles_ok() -> None:
    candles = create_test_candles(5)

    result = FeatureContract.validate(candles, min_count=5)

    assert result.status == ValidationStatus.OK
    assert result.reasons == []
    assert result.candle_count == 5


def test_insufficient_candles_invalid() -> None:
    candles = create_test_candles(10)

    result = FeatureContract.validate(candles)

    assert result.status == ValidationStatus.INVALID
    assert result.candle_count == 10
    assert any("insufficient_candles" in reason for reason in result.reasons)


def test_negative_or_zero_prices_invalid() -> None:
    candles = create_test_candles(5)
    candles[0] = Candle(
        timestamp=candles[0].timestamp,
        open=0.0,
        high=candles[0].high,
        low=candles[0].low,
        close=candles[0].close,
        volume=candles[0].volume,
    )

    result = FeatureContract.validate(candles, min_count=5)

    assert result.status == ValidationStatus.INVALID
    assert "non_positive_prices" in result.reasons


def test_high_less_than_low_invalid() -> None:
    candles = create_test_candles(5)
    candles[0] = Candle(
        timestamp=candles[0].timestamp,
        open=1.1,
        high=1.0,
        low=1.2,
        close=1.15,
        volume=candles[0].volume,
    )

    result = FeatureContract.validate(candles, min_count=5)

    assert result.status == ValidationStatus.INVALID
    assert "high_less_than_low" in result.reasons


def test_open_close_outside_range_invalid() -> None:
    candles = create_test_candles(5)
    candles[0] = Candle(
        timestamp=candles[0].timestamp,
        open=3.0,
        high=2.0,
        low=1.0,
        close=0.5,
        volume=candles[0].volume,
    )

    result = FeatureContract.validate(candles, min_count=5)

    assert result.status == ValidationStatus.INVALID
    assert "open_outside_range" in result.reasons
    assert "close_outside_range" in result.reasons


def test_missing_or_zero_volume_degraded() -> None:
    candles = create_test_candles(5, volume=0.0)

    result = FeatureContract.validate(candles, min_count=5)

    assert result.status == ValidationStatus.DEGRADED
    assert "volume_missing_or_all_zero" in result.reasons


def test_non_monotonic_timestamps_invalid() -> None:
    candles = create_test_candles(5)
    candles[3] = Candle(
        timestamp=candles[1].timestamp,
        open=candles[3].open,
        high=candles[3].high,
        low=candles[3].low,
        close=candles[3].close,
        volume=candles[3].volume,
    )

    result = FeatureContract.validate(candles, min_count=5)

    assert result.status == ValidationStatus.INVALID
    assert "timestamps_not_monotonic_non_decreasing" in result.reasons


def test_duplicate_timestamps_degraded() -> None:
    candles = create_test_candles(5)
    candles[2] = Candle(
        timestamp=candles[1].timestamp,
        open=candles[2].open,
        high=candles[2].high,
        low=candles[2].low,
        close=candles[2].close,
        volume=candles[2].volume,
    )

    result = FeatureContract.validate(candles, min_count=5)

    assert result.status == ValidationStatus.DEGRADED
    assert "duplicate_timestamps" in result.reasons
