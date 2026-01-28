from __future__ import annotations

from datetime import datetime, timedelta

from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe
from src.features.contracts.feature_contract import FeatureContract, ValidationStatus
from src.runtime.jobs.build_features_job import BuildFeaturesJob


class CandleWithoutVolume:
    def __init__(
        self, timestamp: datetime, open_price: float, high: float, low: float, close: float
    ) -> None:
        self.timestamp = timestamp
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close


def create_valid_candles(count: int, *, volume: float = 1000.0) -> list[Candle]:
    candles: list[Candle] = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    for idx in range(count):
        price = 1.1 + (idx * 0.0001)
        candles.append(
            Candle(
                timestamp=base_time + timedelta(hours=idx),
                open=price,
                high=price + 0.001,
                low=price - 0.001,
                close=price + 0.0005,
                volume=volume,
            )
        )

    return candles


def test_contract_missing_volume_populates_missing_and_degraded_flags() -> None:
    candles = [
        CandleWithoutVolume(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            open_price=1.0,
            high=1.1,
            low=0.9,
            close=1.0,
        )
    ]

    result = FeatureContract.validate(candles, min_count=1)  # type: ignore[arg-type]

    assert result.status == ValidationStatus.DEGRADED
    assert "volume" in result.missing_fields
    assert "volume_missing_or_all_zero" in result.degraded_flags


def test_contract_all_zero_volume_sets_degraded_flag() -> None:
    candles = create_valid_candles(10, volume=0.0)

    result = FeatureContract.validate(candles, min_count=1)

    assert result.status == ValidationStatus.DEGRADED
    assert "volume_missing_or_all_zero" in result.degraded_flags


def test_contract_insufficient_for_sma200_marks_missing_sma200() -> None:
    candles = create_valid_candles(50, volume=1000.0)

    result = FeatureContract.validate(candles, min_count=1)

    assert "sma_200" in result.missing_fields
    assert "sma200_slope_pct" in result.missing_fields


def test_build_features_job_persists_completeness_fields_on_snapshot() -> None:
    candles = create_valid_candles(200, volume=0.0)

    job = BuildFeaturesJob()
    result = job.run(symbol="EURUSD", timeframe=Timeframe.H1, candles=candles)

    assert result.ok is True
    assert result.value is not None

    snapshot, _signal = result.value

    assert snapshot.candle_count_used == 200
    assert "volume_missing_or_all_zero" in snapshot.degraded_features
    assert isinstance(snapshot.missing_features, list)
