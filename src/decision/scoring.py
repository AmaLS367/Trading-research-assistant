from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionScores:
    bull_score: float
    bear_score: float
    no_trade_score: float


def calculate_scores(
    indicators: dict[str, object],
    technical_analysis: dict[str, object] | None = None,
) -> DecisionScores:
    bull_score = 0.0
    bear_score = 0.0
    no_trade_score = 0.0

    trend_direction = _get_str(indicators, technical_analysis, "trend_direction")
    trend_strength = _get_float(indicators, technical_analysis, "trend_strength")
    if trend_direction == "BULLISH":
        bull_score += 20.0
        bull_score += _cap(_safe_non_negative(trend_strength) * 0.2, cap=20.0)
    elif trend_direction == "BEARISH":
        bear_score += 20.0
        bear_score += _cap(_safe_non_negative(trend_strength) * 0.2, cap=20.0)
    elif trend_direction == "NEUTRAL":
        no_trade_score += 10.0

    structure = _get_str(indicators, technical_analysis, "structure")
    if structure == "BULLISH":
        bull_score += 15.0
    elif structure == "BEARISH":
        bear_score += 15.0
    elif structure == "RANGE":
        no_trade_score += 10.0

    dist_sma200_pct = _get_float(indicators, technical_analysis, "dist_sma200_pct")
    if dist_sma200_pct is not None:
        if dist_sma200_pct > 0.0:
            bull_score += 10.0
        else:
            bear_score += 10.0

    ema9_sma50_crossover_type = _get_str(
        indicators,
        technical_analysis,
        "ema9_sma50_crossover_type",
    )
    ema9_sma50_crossover_age_bars = _get_float(
        indicators,
        technical_analysis,
        "ema9_sma50_crossover_age_bars",
    )
    if ema9_sma50_crossover_type == "NONE":
        no_trade_score += 5.0
    elif (
        ema9_sma50_crossover_type == "BULLISH"
        and ema9_sma50_crossover_age_bars is not None
        and ema9_sma50_crossover_age_bars <= 10.0
    ):
        bull_score += 10.0
    elif (
        ema9_sma50_crossover_type == "BEARISH"
        and ema9_sma50_crossover_age_bars is not None
        and ema9_sma50_crossover_age_bars <= 10.0
    ):
        bear_score += 10.0

    roc_5 = _get_float(indicators, technical_analysis, "roc_5")
    if roc_5 is not None:
        if roc_5 > 0.0:
            bull_score += 5.0
        elif roc_5 < 0.0:
            bear_score += 5.0

    rsi_delta_1 = _get_float(indicators, technical_analysis, "rsi_delta_1")
    rsi_delta_5 = _get_float(indicators, technical_analysis, "rsi_delta_5")
    if rsi_delta_1 is not None and rsi_delta_5 is not None:
        if rsi_delta_1 > 0.0 and rsi_delta_5 > 0.0:
            bull_score += 5.0
        elif rsi_delta_1 < 0.0 and rsi_delta_5 < 0.0:
            bear_score += 5.0
        else:
            no_trade_score += 5.0

    atr_pct = _get_float(indicators, technical_analysis, "atr_pct")
    bb_squeeze_flag = _get_float(indicators, technical_analysis, "bb_squeeze_flag")
    if (
        atr_pct is not None
        and bb_squeeze_flag is not None
        and atr_pct < 0.08
        and bb_squeeze_flag == 0.0
    ):
        no_trade_score += 20.0

    return DecisionScores(
        bull_score=_clamp_score(bull_score),
        bear_score=_clamp_score(bear_score),
        no_trade_score=_clamp_score(no_trade_score),
    )


def _get_value(
    indicators: dict[str, object],
    technical_analysis: dict[str, object] | None,
    key: str,
) -> object | None:
    if key in indicators:
        return indicators.get(key)
    if technical_analysis is None:
        return None
    if key in technical_analysis:
        return technical_analysis.get(key)
    return None


def _get_str(
    indicators: dict[str, object],
    technical_analysis: dict[str, object] | None,
    key: str,
) -> str | None:
    value = _get_value(indicators, technical_analysis, key)
    if not isinstance(value, str):
        return None
    return value.strip().upper()


def _get_float(
    indicators: dict[str, object],
    technical_analysis: dict[str, object] | None,
    key: str,
) -> float | None:
    value = _get_value(indicators, technical_analysis, key)
    if value is None:
        return None

    if isinstance(value, bool):
        return float(value)

    if isinstance(value, (int, float)):
        as_float = float(value)
        if math.isnan(as_float) or math.isinf(as_float):
            return None
        return as_float

    try:
        as_float = float(value)  # type: ignore[arg-type]
    except Exception:
        return None

    if math.isnan(as_float) or math.isinf(as_float):
        return None
    return as_float


def _safe_non_negative(value: float | None) -> float:
    if value is None:
        return 0.0
    if value < 0.0:
        return 0.0
    return value


def _cap(value: float, cap: float) -> float:
    if value > cap:
        return cap
    return value


def _clamp_score(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 100.0:
        return 100.0
    return float(value)
