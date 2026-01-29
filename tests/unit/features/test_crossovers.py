from __future__ import annotations

from datetime import datetime, timedelta

from src.core.models.candle import Candle
from src.features.signals.crossovers import detect_crossovers


def create_test_candles(closes: list[float]) -> list[Candle]:
    candles: list[Candle] = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    for idx, close in enumerate(closes):
        candles.append(
            Candle(
                timestamp=base_time + timedelta(hours=idx),
                open=close,
                high=close,
                low=close,
                close=close,
                volume=1000.0,
            )
        )

    return candles


def test_ema9_sma50_bullish_crossover_detected_age_zero() -> None:
    closes = [100.0 for _ in range(260)]
    closes[-2] = 90.0
    closes[-1] = 200.0
    candles = create_test_candles(closes)

    result = detect_crossovers(candles, lookback_bars=50)

    assert result["ema9_sma50_crossover_type"] == "BULLISH"
    assert result["ema9_sma50_crossover_age_bars"] == 0


def test_ema9_sma50_no_crossover_returns_none_age_minus_one() -> None:
    candles = create_test_candles([100.0 for _ in range(260)])

    result = detect_crossovers(candles, lookback_bars=50)

    assert result["ema9_sma50_crossover_type"] == "NONE"
    assert result["ema9_sma50_crossover_age_bars"] == -1


def test_sma50_sma200_golden_cross_detected_age_zero() -> None:
    closes: list[float] = []
    closes.extend([1.0 for _ in range(60)])
    closes.extend([200.0 for _ in range(150)])
    closes.extend([1.0 for _ in range(49)])
    closes.append(10000.0)
    assert len(closes) == 260

    candles = create_test_candles(closes)

    result = detect_crossovers(candles, lookback_bars=50)

    assert result["sma50_sma200_crossover_type"] == "GOLDEN"
    assert result["sma50_sma200_crossover_age_bars"] == 0


def test_output_contains_required_keys_and_types() -> None:
    candles = create_test_candles([100.0 for _ in range(260)])

    result = detect_crossovers(candles, lookback_bars=50)

    assert set(result.keys()) == {
        "ema9_sma50_crossover_type",
        "ema9_sma50_crossover_age_bars",
        "sma50_sma200_crossover_type",
        "sma50_sma200_crossover_age_bars",
    }
    assert isinstance(result["ema9_sma50_crossover_type"], str)
    assert isinstance(result["ema9_sma50_crossover_age_bars"], int)
    assert isinstance(result["sma50_sma200_crossover_type"], str)
    assert isinstance(result["sma50_sma200_crossover_age_bars"], int)
