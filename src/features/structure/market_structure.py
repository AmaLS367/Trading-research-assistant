from __future__ import annotations

import math

from src.features.structure.swing_points import SwingPoint


def classify_structure(swings: list[SwingPoint]) -> dict[str, object]:
    try:
        sorted_swings = sorted(swings, key=lambda sp: sp.index)
    except Exception:
        sorted_swings = swings

    highs = [sp for sp in sorted_swings if sp.type == "HIGH"]
    lows = [sp for sp in sorted_swings if sp.type == "LOW"]

    if len(highs) < 2 or len(lows) < 2:
        return {"structure": "RANGE", "confidence": 0.0}

    prev_high = highs[-2]
    last_high = highs[-1]
    prev_low = lows[-2]
    last_low = lows[-1]

    try:
        prev_high_price = float(prev_high.price)
        last_high_price = float(last_high.price)
        prev_low_price = float(prev_low.price)
        last_low_price = float(last_low.price)
    except Exception:
        return {"structure": "RANGE", "confidence": 0.0}

    if not all(
        math.isfinite(value)
        for value in [prev_high_price, last_high_price, prev_low_price, last_low_price]
    ):
        return {"structure": "RANGE", "confidence": 0.0}

    hh = last_high_price > prev_high_price
    lh = last_high_price < prev_high_price
    hl = last_low_price > prev_low_price
    ll = last_low_price < prev_low_price

    if hh and hl:
        structure = "BULLISH"
    elif lh and ll:
        structure = "BEARISH"
    else:
        structure = "RANGE"

    if structure == "RANGE":
        confidence = 40.0
    else:
        confidence = 60.0

        if prev_high_price == 0.0:
            high_delta_pct = 0.0
        else:
            high_delta_pct = (abs(last_high_price - prev_high_price) / abs(prev_high_price)) * 100.0

        if prev_low_price == 0.0:
            low_delta_pct = 0.0
        else:
            low_delta_pct = (abs(last_low_price - prev_low_price) / abs(prev_low_price)) * 100.0

        delta_score = min(40.0, (high_delta_pct + low_delta_pct) * 2.0)
        confidence = confidence + delta_score

    if confidence < 0.0:
        confidence = 0.0
    if confidence > 100.0:
        confidence = 100.0

    return {"structure": structure, "confidence": float(confidence)}
