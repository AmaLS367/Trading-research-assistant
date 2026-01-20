from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.core.models.candle import Candle
from src.features.volume.volume_features import calculate_volume_features


def create_test_candles(volumes: list[float]) -> list[Candle]:
    candles: list[Candle] = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    for idx, volume in enumerate(volumes):
        candles.append(
            Candle(
                timestamp=base_time + timedelta(hours=idx),
                open=1.0,
                high=1.0,
                low=1.0,
                close=1.0,
                volume=volume,
            )
        )

    return candles


def test_all_zeros_returns_unknown_and_zero_zscore() -> None:
    candles = create_test_candles([0.0 for _ in range(30)])

    result = calculate_volume_features(candles, window=20)

    assert result["volume_trend"] == "UNKNOWN"
    assert result["volume_zscore"] == 0.0
    assert result["volume_confirmation_flag"] == 0.0


def test_rising_volume_trend_detected() -> None:
    volumes = [100.0 for _ in range(25)]
    volumes.extend([120.0 for _ in range(5)])
    candles = create_test_candles(volumes)

    result = calculate_volume_features(candles, window=20)

    assert result["volume_trend"] == "RISING"


def test_std_zero_returns_zero_zscore() -> None:
    candles = create_test_candles([100.0 for _ in range(30)])

    result = calculate_volume_features(candles, window=20)

    assert result["volume_zscore"] == 0.0
    assert result["volume_confirmation_flag"] == 0.0


def test_confirmation_flag_set_when_zscore_high() -> None:
    volumes = [100.0 for _ in range(19)]
    volumes.append(200.0)
    candles = create_test_candles(volumes)

    result = calculate_volume_features(candles, window=20)

    assert result["volume_confirmation_flag"] == 1.0
    assert result["volume_zscore"] >= 1.0


def test_output_types_and_keys() -> None:
    candles = create_test_candles([100.0 for _ in range(30)])

    result = calculate_volume_features(candles, window=20)

    assert set(result.keys()) == {
        "volume_mean",
        "volume_zscore",
        "volume_trend",
        "volume_confirmation_flag",
    }
    assert isinstance(result["volume_mean"], float)
    assert isinstance(result["volume_zscore"], float)
    assert isinstance(result["volume_trend"], str)
    assert result["volume_trend"] in {"RISING", "FALLING", "FLAT", "UNKNOWN"}
    assert isinstance(result["volume_confirmation_flag"], float)
    assert result["volume_confirmation_flag"] in {0.0, 1.0}

    assert result["volume_mean"] == pytest.approx(100.0)
