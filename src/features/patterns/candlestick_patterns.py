from __future__ import annotations

import math

from src.core.models.candle import Candle


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        result = float(value)  # type: ignore[arg-type]
    except Exception:
        return default

    if not math.isfinite(result):
        return default

    return result


def _candle_metrics(candle: Candle) -> dict[str, float]:
    open_price = _safe_float(getattr(candle, "open", 0.0))
    close_price = _safe_float(getattr(candle, "close", 0.0))
    high_price = _safe_float(getattr(candle, "high", 0.0))
    low_price = _safe_float(getattr(candle, "low", 0.0))

    body = abs(close_price - open_price)
    candle_range = high_price - low_price
    if candle_range < 0.0:
        candle_range = 0.0

    upper_wick = high_price - max(open_price, close_price)
    if upper_wick < 0.0:
        upper_wick = 0.0

    lower_wick = min(open_price, close_price) - low_price
    if lower_wick < 0.0:
        lower_wick = 0.0

    return {
        "open": open_price,
        "close": close_price,
        "high": high_price,
        "low": low_price,
        "body": body,
        "range": candle_range,
        "upper_wick": upper_wick,
        "lower_wick": lower_wick,
    }


def detect_candlestick_patterns(candles: list[Candle]) -> dict[str, object]:
    result = {
        "candlestick_pattern": "NONE",
        "candlestick_pattern_strength": 0.0,
    }

    if not candles:
        return result

    last = _candle_metrics(candles[-1])

    body_ratio = last["body"] / last["range"] if last["range"] > 0.0 else 0.0

    is_doji = (last["range"] > 0.0) and (body_ratio <= 0.1)
    is_big_body = (last["range"] > 0.0) and (body_ratio >= 0.7)

    if len(candles) < 2:
        if is_big_body:
            return {
                "candlestick_pattern": "BIG_BODY",
                "candlestick_pattern_strength": float(max(0.0, min(100.0, body_ratio * 100.0))),
            }
        if is_doji:
            doji_strength = ((0.1 - body_ratio) / 0.1) * 100.0
            return {
                "candlestick_pattern": "DOJI",
                "candlestick_pattern_strength": float(max(0.0, min(100.0, doji_strength))),
            }
        return result

    prev = _candle_metrics(candles[-2])

    last_bullish = last["close"] > last["open"]
    last_bearish = last["close"] < last["open"]
    last_neutral = last["close"] == last["open"]

    prev_body = prev["body"]
    last_body = last["body"]

    bull_engulf = last_bullish and (last["open"] < prev["close"]) and (last["close"] > prev["open"])
    bear_engulf = last_bearish and (last["open"] > prev["close"]) and (last["close"] < prev["open"])

    bull_pin = (last_bullish or last_neutral) and (
        last["lower_wick"] >= 2.0 * last_body and last["upper_wick"] <= last_body
    )
    bear_pin = (last_bearish or last_neutral) and (
        last["upper_wick"] >= 2.0 * last_body and last["lower_wick"] <= last_body
    )

    inside_bar = (last["high"] <= prev["high"]) and (last["low"] >= prev["low"])

    if bull_engulf or bear_engulf:
        pattern = "BULL_ENGULF" if bull_engulf else "BEAR_ENGULF"
        if prev_body == 0.0:
            strength = 100.0 if last_body > 0.0 else 0.0
        else:
            strength = min(100.0, (last_body / prev_body) * 50.0)
        return {"candlestick_pattern": pattern, "candlestick_pattern_strength": float(strength)}

    if bull_pin or bear_pin:
        if bull_pin and bear_pin:
            pattern = "BULL_PIN" if last["lower_wick"] >= last["upper_wick"] else "BEAR_PIN"
        else:
            pattern = "BULL_PIN" if bull_pin else "BEAR_PIN"

        wick = last["lower_wick"] if pattern == "BULL_PIN" else last["upper_wick"]
        if last_body == 0.0:
            strength = 100.0 if wick > 0.0 else 0.0
        else:
            strength = min(100.0, (wick / last_body) * 25.0)
        return {"candlestick_pattern": pattern, "candlestick_pattern_strength": float(strength)}

    if inside_bar:
        return {"candlestick_pattern": "INSIDE_BAR", "candlestick_pattern_strength": 40.0}

    if is_big_body:
        strength = max(0.0, min(100.0, body_ratio * 100.0))
        return {"candlestick_pattern": "BIG_BODY", "candlestick_pattern_strength": float(strength)}

    if is_doji:
        doji_strength = ((0.1 - body_ratio) / 0.1) * 100.0
        doji_strength = max(0.0, min(100.0, doji_strength))
        return {"candlestick_pattern": "DOJI", "candlestick_pattern_strength": float(doji_strength)}

    return result
