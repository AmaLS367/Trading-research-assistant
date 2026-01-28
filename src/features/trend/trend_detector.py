from __future__ import annotations

import math

from src.core.models.candle import Candle


class TrendDetector:
    @staticmethod
    def detect(candles: list[Candle], indicators: dict[str, float]) -> dict[str, object]:
        default = {"trend_direction": "NEUTRAL", "trend_strength": 0.0}

        if not candles:
            return default

        required_keys = [
            "sma_50",
            "sma_200",
            "sma50_slope_pct",
            "sma200_slope_pct",
        ]
        for key in required_keys:
            if key not in indicators:
                return default

        try:
            close = float(candles[-1].close)
            sma_50 = float(indicators["sma_50"])
            sma_200 = float(indicators["sma_200"])
            sma50_slope_pct = float(indicators["sma50_slope_pct"])
            sma200_slope_pct = float(indicators["sma200_slope_pct"])
        except Exception:
            return default

        if sma_50 == 0.0 or sma_200 == 0.0:
            return default

        if not all(
            math.isfinite(value)
            for value in [close, sma_50, sma_200, sma50_slope_pct, sma200_slope_pct]
        ):
            return default

        price_above_sma200 = close > sma_200
        price_below_sma200 = close < sma_200
        sma50_above_sma200 = sma_50 > sma_200
        sma50_below_sma200 = sma_50 < sma_200
        slopes_bullish = (sma50_slope_pct > 0.0) and (sma200_slope_pct > 0.0)
        slopes_bearish = (sma50_slope_pct < 0.0) and (sma200_slope_pct < 0.0)

        if price_above_sma200 and sma50_above_sma200 and slopes_bullish:
            trend_direction = "BULLISH"
        elif price_below_sma200 and sma50_below_sma200 and slopes_bearish:
            trend_direction = "BEARISH"
        else:
            trend_direction = "NEUTRAL"

        slope_magnitude = abs(sma50_slope_pct) + abs(sma200_slope_pct)
        trend_strength = min(100.0, slope_magnitude * 100.0)

        if trend_direction == "NEUTRAL":
            trend_strength = min(trend_strength, 40.0)

        if trend_strength < 0.0:
            trend_strength = 0.0
        if trend_strength > 100.0:
            trend_strength = 100.0

        return {
            "trend_direction": trend_direction,
            "trend_strength": float(trend_strength),
        }
