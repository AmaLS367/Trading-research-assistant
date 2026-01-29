from __future__ import annotations

import pytest

from src.decision.reason_codes import (
    INSUFFICIENT_DATA,
    LOW_VOLATILITY_NO_SQUEEZE,
    NO_FRESH_CROSSOVER,
    RANGE_STRUCTURE,
    WEAK_MOMENTUM,
    build_reason_codes,
)
from src.decision.scoring import DecisionScores

pytestmark = pytest.mark.unit


def test_adds_low_volatility_no_squeeze_reason() -> None:
    indicators: dict[str, object] = {
        "atr_pct": 0.05,
        "bb_squeeze_flag": 0.0,
    }

    codes = build_reason_codes(indicators, scores=DecisionScores(0.0, 0.0, 0.0))

    assert LOW_VOLATILITY_NO_SQUEEZE in codes


def test_adds_no_fresh_crossover_when_both_none() -> None:
    indicators: dict[str, object] = {
        "ema9_sma50_crossover_type": "NONE",
        "ema9_sma50_crossover_age_bars": -1,
        "sma50_sma200_crossover_type": "NONE",
        "sma50_sma200_crossover_age_bars": -1,
    }

    codes = build_reason_codes(indicators, scores=DecisionScores(0.0, 0.0, 0.0))

    assert NO_FRESH_CROSSOVER in codes


def test_adds_no_fresh_crossover_when_both_old() -> None:
    indicators: dict[str, object] = {
        "ema9_sma50_crossover_type": "BULLISH",
        "ema9_sma50_crossover_age_bars": 11,
        "sma50_sma200_crossover_type": "GOLDEN",
        "sma50_sma200_crossover_age_bars": 50,
    }

    codes = build_reason_codes(indicators, scores=DecisionScores(0.0, 0.0, 0.0))

    assert NO_FRESH_CROSSOVER in codes


def test_adds_weak_momentum_when_roc_missing() -> None:
    indicators: dict[str, object] = {}

    codes = build_reason_codes(indicators, scores=DecisionScores(0.0, 0.0, 0.0))

    assert WEAK_MOMENTUM in codes


def test_adds_weak_momentum_when_roc_is_small() -> None:
    indicators: dict[str, object] = {
        "roc_5": 0.0,
        "roc_20": 0.0,
    }

    codes = build_reason_codes(indicators, scores=DecisionScores(0.0, 0.0, 0.0))

    assert WEAK_MOMENTUM in codes


def test_adds_range_structure_when_structure_is_range() -> None:
    indicators: dict[str, object] = {
        "structure": "RANGE",
    }

    codes = build_reason_codes(indicators, scores=DecisionScores(0.0, 0.0, 0.0))

    assert RANGE_STRUCTURE in codes


def test_adds_insufficient_data_when_candle_count_used_below_200() -> None:
    indicators: dict[str, object] = {
        "candle_count_used": 199,
    }

    codes = build_reason_codes(indicators, scores=DecisionScores(0.0, 0.0, 0.0))

    assert INSUFFICIENT_DATA in codes


def test_adds_insufficient_data_when_validation_status_degraded() -> None:
    indicators: dict[str, object] = {
        "validation_status": "DEGRADED",
    }

    codes = build_reason_codes(indicators, scores=DecisionScores(0.0, 0.0, 0.0))

    assert INSUFFICIENT_DATA in codes
