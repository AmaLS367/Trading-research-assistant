from __future__ import annotations

import math

from src.decision.scoring import DecisionScores

CONFLICT_TREND_STRUCTURE = "CONFLICT_TREND_STRUCTURE"
NO_FRESH_CROSSOVER = "NO_FRESH_CROSSOVER"
WEAK_MOMENTUM = "WEAK_MOMENTUM"
BB_MIDZONE = "BB_MIDZONE"
LOW_VOLATILITY_NO_SQUEEZE = "LOW_VOLATILITY_NO_SQUEEZE"
RANGE_STRUCTURE = "RANGE_STRUCTURE"
PARSING_FAILED = "PARSING_FAILED"
INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


def build_reason_codes(indicators: dict[str, object], scores: DecisionScores) -> list[str]:
    _ = scores

    reason_codes: list[str] = []

    if _is_low_volatility_no_squeeze(indicators):
        _append_once(reason_codes, LOW_VOLATILITY_NO_SQUEEZE)

    if _is_no_fresh_crossover(indicators):
        _append_once(reason_codes, NO_FRESH_CROSSOVER)

    if _is_weak_momentum(indicators):
        _append_once(reason_codes, WEAK_MOMENTUM)

    if _get_str(indicators, "structure") == "RANGE":
        _append_once(reason_codes, RANGE_STRUCTURE)

    if _is_insufficient_data(indicators):
        _append_once(reason_codes, INSUFFICIENT_DATA)

    return reason_codes


def _append_once(reason_codes: list[str], code: str) -> None:
    if code in reason_codes:
        return
    reason_codes.append(code)


def _get_str(indicators: dict[str, object], key: str) -> str | None:
    value = indicators.get(key)
    if not isinstance(value, str):
        return None
    return value.strip().upper()


def _get_float(indicators: dict[str, object], key: str) -> float | None:
    value = indicators.get(key)
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


def _is_low_volatility_no_squeeze(indicators: dict[str, object]) -> bool:
    atr_pct = _get_float(indicators, "atr_pct")
    bb_squeeze_flag = _get_float(indicators, "bb_squeeze_flag")
    if atr_pct is None or bb_squeeze_flag is None:
        return False
    return atr_pct < 0.08 and bb_squeeze_flag == 0.0


def _has_fresh_crossover(indicators: dict[str, object], type_key: str, age_key: str) -> bool:
    crossover_type = _get_str(indicators, type_key)
    age_bars = _get_float(indicators, age_key)

    if crossover_type is None:
        return False
    if crossover_type == "NONE":
        return False
    if age_bars is None:
        return False
    return age_bars <= 10.0


def _is_no_fresh_crossover(indicators: dict[str, object]) -> bool:
    ema_fresh = _has_fresh_crossover(
        indicators,
        type_key="ema9_sma50_crossover_type",
        age_key="ema9_sma50_crossover_age_bars",
    )
    sma_fresh = _has_fresh_crossover(
        indicators,
        type_key="sma50_sma200_crossover_type",
        age_key="sma50_sma200_crossover_age_bars",
    )
    return not ema_fresh and not sma_fresh


def _is_weak_momentum(indicators: dict[str, object]) -> bool:
    roc_5 = _get_float(indicators, "roc_5")
    roc_20 = _get_float(indicators, "roc_20")
    if roc_5 is None or roc_20 is None:
        return True
    return abs(roc_5) < 0.02 and abs(roc_20) < 0.05


def _is_insufficient_data(indicators: dict[str, object]) -> bool:
    candle_count_used = _get_float(indicators, "candle_count_used")
    if candle_count_used is not None and candle_count_used < 200.0:
        return True

    validation_status = indicators.get("validation_status")
    if isinstance(validation_status, str):
        status_text = validation_status.strip().upper()
    else:
        status_text = (
            str(validation_status).strip().upper() if validation_status is not None else ""
        )

    if status_text in {"DEGRADED", "INVALID"}:
        return True

    return status_text.endswith(".DEGRADED") or status_text.endswith(".INVALID")
