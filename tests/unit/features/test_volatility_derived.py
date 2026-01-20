from __future__ import annotations

import pytest

from src.features.derived.volatility_derived import (
    BB_SQUEEZE_BANDWIDTH_PCT_THRESHOLD,
    calculate_bb_metrics,
)


def test_computes_bb_position_and_clamps() -> None:
    indicators = {"bb_upper": 120.0, "bb_middle": 110.0, "bb_lower": 100.0}

    inside = calculate_bb_metrics(110.0, indicators)
    assert inside["bb_position"] == pytest.approx(0.5)

    below = calculate_bb_metrics(90.0, indicators)
    assert below["bb_position"] == 0.0

    above = calculate_bb_metrics(130.0, indicators)
    assert above["bb_position"] == 1.0


def test_computes_bb_bandwidth_pct() -> None:
    indicators = {"bb_upper": 120.0, "bb_middle": 110.0, "bb_lower": 100.0}

    result = calculate_bb_metrics(110.0, indicators)

    expected = ((120.0 - 100.0) / 110.0) * 100.0
    assert result["bb_bandwidth_pct"] == pytest.approx(expected)


def test_sets_bb_squeeze_flag_below_and_above_threshold() -> None:
    below_threshold = {
        "bb_upper": 100.1,
        "bb_middle": 100.0,
        "bb_lower": 100.0,
    }
    below = calculate_bb_metrics(100.0, below_threshold)
    assert below["bb_bandwidth_pct"] < BB_SQUEEZE_BANDWIDTH_PCT_THRESHOLD
    assert below["bb_squeeze_flag"] == 1.0

    above_threshold = {
        "bb_upper": 101.0,
        "bb_middle": 100.0,
        "bb_lower": 99.0,
    }
    above = calculate_bb_metrics(100.0, above_threshold)
    assert above["bb_bandwidth_pct"] > BB_SQUEEZE_BANDWIDTH_PCT_THRESHOLD
    assert above["bb_squeeze_flag"] == 0.0


def test_missing_keys_returns_all_zero() -> None:
    result = calculate_bb_metrics(100.0, {})

    assert result == {
        "bb_position": 0.0,
        "bb_bandwidth_pct": 0.0,
        "bb_squeeze_flag": 0.0,
        "atr_pct": 0.0,
    }


def test_handles_bb_upper_equals_bb_lower_and_bb_middle_zero_safely() -> None:
    equal_bands = {"bb_upper": 100.0, "bb_middle": 100.0, "bb_lower": 100.0}
    equal_result = calculate_bb_metrics(100.0, equal_bands)
    assert equal_result["bb_position"] == 0.0

    zero_middle = {"bb_upper": 110.0, "bb_middle": 0.0, "bb_lower": 100.0}
    zero_middle_result = calculate_bb_metrics(105.0, zero_middle)
    assert zero_middle_result["bb_bandwidth_pct"] == 0.0


def test_computes_atr_pct_correctly() -> None:
    indicators = {
        "bb_upper": 120.0,
        "bb_middle": 110.0,
        "bb_lower": 100.0,
        "atr": 2.2,
    }

    result = calculate_bb_metrics(110.0, indicators)

    assert result["atr_pct"] == pytest.approx((2.2 / 110.0) * 100.0)


def test_missing_atr_returns_zero() -> None:
    indicators = {"bb_upper": 120.0, "bb_middle": 110.0, "bb_lower": 100.0}

    result = calculate_bb_metrics(110.0, indicators)

    assert result["atr_pct"] == 0.0


def test_close_price_zero_returns_zero_atr_pct_without_crashing() -> None:
    indicators = {
        "bb_upper": 120.0,
        "bb_middle": 110.0,
        "bb_lower": 100.0,
        "atr": 2.2,
    }

    result = calculate_bb_metrics(0.0, indicators)

    assert result["atr_pct"] == 0.0
