from __future__ import annotations

BB_SQUEEZE_BANDWIDTH_PCT_THRESHOLD = 0.2


def calculate_bb_metrics(close_price: float, indicators: dict[str, float]) -> dict[str, float]:
    output = {
        "bb_position": 0.0,
        "bb_bandwidth_pct": 0.0,
        "bb_squeeze_flag": 0.0,
        "atr_pct": 0.0,
    }

    if (
        "bb_upper" not in indicators
        or "bb_middle" not in indicators
        or "bb_lower" not in indicators
    ):
        return output

    try:
        close_float = float(close_price)
        bb_upper = float(indicators["bb_upper"])
        bb_middle = float(indicators["bb_middle"])
        bb_lower = float(indicators["bb_lower"])
    except Exception:
        return output

    if bb_upper > bb_lower:
        position = (close_float - bb_lower) / (bb_upper - bb_lower)
        if position < 0.0:
            position = 0.0
        if position > 1.0:
            position = 1.0
        output["bb_position"] = float(position)

    if bb_middle != 0.0:
        output["bb_bandwidth_pct"] = float(((bb_upper - bb_lower) / bb_middle) * 100.0)

    atr_value = indicators.get("atr")
    if close_float != 0.0 and atr_value is not None:
        try:
            atr_float = float(atr_value)
        except Exception:
            atr_float = 0.0

        if atr_float > 0.0:
            output["atr_pct"] = float((atr_float / close_float) * 100.0)

    if output["bb_bandwidth_pct"] < BB_SQUEEZE_BANDWIDTH_PCT_THRESHOLD:
        output["bb_squeeze_flag"] = 1.0

    return output
