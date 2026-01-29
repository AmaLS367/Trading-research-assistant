from __future__ import annotations

import pytest

from src.decision.scoring import calculate_scores

pytestmark = pytest.mark.unit


def test_bullish_scenario_scores_bull_higher_than_bear() -> None:
    indicators: dict[str, object] = {
        "trend_direction": "BULLISH",
        "trend_strength": 80.0,
        "structure": "BULLISH",
        "dist_sma200_pct": 1.0,
        "ema9_sma50_crossover_type": "BULLISH",
        "ema9_sma50_crossover_age_bars": 2,
        "roc_5": 1.2,
        "rsi_delta_1": 0.5,
        "rsi_delta_5": 0.2,
        "atr_pct": 1.0,
        "bb_squeeze_flag": 1.0,
    }

    scores = calculate_scores(indicators)

    assert scores.bull_score > scores.bear_score
    assert scores.bull_score > 0.0


def test_bearish_scenario_scores_bear_higher_than_bull() -> None:
    indicators: dict[str, object] = {
        "trend_direction": "BEARISH",
        "trend_strength": 70.0,
        "structure": "BEARISH",
        "dist_sma200_pct": -2.0,
        "ema9_sma50_crossover_type": "BEARISH",
        "ema9_sma50_crossover_age_bars": 1,
        "roc_5": -0.6,
        "rsi_delta_1": -0.4,
        "rsi_delta_5": -0.3,
        "atr_pct": 1.0,
        "bb_squeeze_flag": 1.0,
    }

    scores = calculate_scores(indicators)

    assert scores.bear_score > scores.bull_score
    assert scores.bear_score > 0.0


def test_low_volatility_no_squeeze_yields_high_no_trade_score() -> None:
    indicators: dict[str, object] = {
        "trend_direction": "NEUTRAL",
        "atr_pct": 0.05,
        "bb_squeeze_flag": 0.0,
        "ema9_sma50_crossover_type": "NONE",
    }

    scores = calculate_scores(indicators)

    assert scores.no_trade_score >= 20.0


def test_missing_keys_does_not_crash_and_scores_are_clamped() -> None:
    scores = calculate_scores({}, technical_analysis=None)

    assert 0.0 <= scores.bull_score <= 100.0
    assert 0.0 <= scores.bear_score <= 100.0
    assert 0.0 <= scores.no_trade_score <= 100.0
