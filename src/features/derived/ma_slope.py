from __future__ import annotations

import math

import pandas as pd

from src.core.models.candle import Candle
from src.features.math.slope import calculate_normalized_slope


def calculate_ma_slopes(candles: list[Candle], slope_window: int = 10) -> dict[str, float]:
    output = {
        "sma50_slope_pct": 0.0,
        "sma200_slope_pct": 0.0,
        "ema9_slope_pct": 0.0,
    }

    if len(candles) < 2:
        return output

    try:
        close = pd.Series([candle.close for candle in candles], dtype=float)

        sma_50 = close.rolling(window=50).mean()
        sma_200 = close.rolling(window=200).mean()
        ema_9 = close.ewm(span=9, adjust=False).mean()

        sma50_slope = float(calculate_normalized_slope(sma_50, window=slope_window))
        sma200_slope = float(calculate_normalized_slope(sma_200, window=slope_window))
        ema9_slope = float(calculate_normalized_slope(ema_9, window=slope_window))

        if not math.isfinite(sma50_slope):
            sma50_slope = 0.0
        if not math.isfinite(sma200_slope):
            sma200_slope = 0.0
        if not math.isfinite(ema9_slope):
            ema9_slope = 0.0

        return {
            "sma50_slope_pct": sma50_slope,
            "sma200_slope_pct": sma200_slope,
            "ema9_slope_pct": ema9_slope,
        }
    except Exception:
        return output
