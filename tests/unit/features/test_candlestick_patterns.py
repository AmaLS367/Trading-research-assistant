from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.core.models.candle import Candle
from src.features.patterns.candlestick_patterns import detect_candlestick_patterns


def make_candle(
    timestamp: datetime,
    *,
    open_price: float,
    high_price: float,
    low_price: float,
    close_price: float,
) -> Candle:
    return Candle(
        timestamp=timestamp,
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        volume=1000.0,
    )


def test_doji_detected_single_candle() -> None:
    candle = make_candle(
        datetime(2024, 1, 1, 12, 0, 0),
        open_price=100.0,
        high_price=105.0,
        low_price=95.0,
        close_price=100.5,
    )

    result = detect_candlestick_patterns([candle])

    assert result["candlestick_pattern"] == "DOJI"
    assert isinstance(result["candlestick_pattern_strength"], float)
    assert 0.0 <= result["candlestick_pattern_strength"] <= 100.0


def test_bull_engulfing_detected() -> None:
    t0 = datetime(2024, 1, 1, 12, 0, 0)
    prev = make_candle(
        t0,
        open_price=105.0,
        high_price=106.0,
        low_price=99.0,
        close_price=100.0,
    )
    last = make_candle(
        t0 + timedelta(hours=1),
        open_price=99.0,
        high_price=107.0,
        low_price=98.0,
        close_price=106.0,
    )

    result = detect_candlestick_patterns([prev, last])

    assert result["candlestick_pattern"] == "BULL_ENGULF"
    assert result["candlestick_pattern_strength"] == pytest.approx(70.0)


def test_inside_bar_detected() -> None:
    t0 = datetime(2024, 1, 1, 12, 0, 0)
    prev = make_candle(
        t0,
        open_price=105.0,
        high_price=110.0,
        low_price=90.0,
        close_price=100.0,
    )
    last = make_candle(
        t0 + timedelta(hours=1),
        open_price=101.0,
        high_price=105.0,
        low_price=95.0,
        close_price=102.0,
    )

    result = detect_candlestick_patterns([prev, last])

    assert result["candlestick_pattern"] == "INSIDE_BAR"
    assert result["candlestick_pattern_strength"] == 40.0


def test_pin_bar_detected() -> None:
    t0 = datetime(2024, 1, 1, 12, 0, 0)
    prev = make_candle(
        t0,
        open_price=101.0,
        high_price=101.0,
        low_price=91.0,
        close_price=100.5,
    )
    last = make_candle(
        t0 + timedelta(hours=1),
        open_price=100.0,
        high_price=102.0,
        low_price=90.0,
        close_price=101.0,
    )

    result = detect_candlestick_patterns([prev, last])

    assert result["candlestick_pattern"] == "BULL_PIN"
    assert isinstance(result["candlestick_pattern_strength"], float)
    assert result["candlestick_pattern_strength"] > 0.0


def test_priority_inside_bar_over_doji() -> None:
    t0 = datetime(2024, 1, 1, 12, 0, 0)
    prev = make_candle(
        t0,
        open_price=100.0,
        high_price=105.0,
        low_price=95.0,
        close_price=100.0,
    )
    last = make_candle(
        t0 + timedelta(hours=1),
        open_price=100.0,
        high_price=101.0,
        low_price=99.9,
        close_price=100.1,
    )

    result = detect_candlestick_patterns([prev, last])

    assert result["candlestick_pattern"] == "INSIDE_BAR"
    assert result["candlestick_pattern_strength"] == 40.0
