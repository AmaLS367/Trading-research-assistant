from __future__ import annotations

from datetime import datetime, timedelta

from src.core.models.candle import Candle
from src.core.models.timeframe import Timeframe
from src.runtime.jobs.build_features_job import BuildFeaturesJob


def create_test_candles(count: int = 260) -> list[Candle]:
    candles: list[Candle] = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    for idx in range(count):
        base_price = 1.1000 + (idx * 0.0001)
        candles.append(
            Candle(
                timestamp=base_time + timedelta(hours=idx),
                open=base_price,
                high=base_price + 0.0010,
                low=base_price - 0.0010,
                close=base_price + 0.0005,
                volume=1000.0 + float(idx),
            )
        )

    return candles


def test_build_features_job_integration_outputs_expected_keys() -> None:
    candles = create_test_candles(260)

    job = BuildFeaturesJob()
    result = job.run(symbol="EURUSD", timeframe=Timeframe.H1, candles=candles)

    assert result.ok is True
    assert result.value is not None

    snapshot, _signal = result.value
    indicators = snapshot.indicators

    for key in ["sma_50", "sma_200", "ema_9", "rsi"]:
        assert key in indicators
        assert isinstance(indicators[key], float)

    for key in ["price_change_pct_1", "price_change_pct_5"]:
        assert key in indicators
        assert isinstance(indicators[key], float)

    assert "dist_sma50_pct" in indicators
    assert isinstance(indicators["dist_sma50_pct"], float)

    for key in ["bb_position", "bb_bandwidth_pct", "atr_pct"]:
        assert key in indicators
        assert isinstance(indicators[key], float)

    for key in ["rsi_delta_1", "roc_5"]:
        assert key in indicators
        assert isinstance(indicators[key], float)

    assert "sma50_slope_pct" in indicators
    assert isinstance(indicators["sma50_slope_pct"], float)

    assert snapshot.trend_direction in {"BULLISH", "BEARISH", "NEUTRAL", None}
    assert snapshot.trend_strength is None or isinstance(snapshot.trend_strength, float)

    assert isinstance(snapshot.ema9_sma50_crossover_type, str) or snapshot.ema9_sma50_crossover_type is None
    assert (
        isinstance(snapshot.ema9_sma50_crossover_age_bars, int)
        or snapshot.ema9_sma50_crossover_age_bars is None
    )
    assert isinstance(snapshot.sma50_sma200_crossover_type, str) or snapshot.sma50_sma200_crossover_type is None
    assert (
        isinstance(snapshot.sma50_sma200_crossover_age_bars, int)
        or snapshot.sma50_sma200_crossover_age_bars is None
    )

    assert "ema9_sma50_crossover_age_bars" in indicators
    assert isinstance(indicators["ema9_sma50_crossover_age_bars"], float)
    assert "sma50_sma200_crossover_age_bars" in indicators
    assert isinstance(indicators["sma50_sma200_crossover_age_bars"], float)
