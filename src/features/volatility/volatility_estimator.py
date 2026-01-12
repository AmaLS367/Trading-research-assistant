from src.core.models.candle import Candle
from src.features.indicators.indicator_engine import calculate_features


class VolatilityEstimator:
    @staticmethod
    def estimate(candles: list[Candle]) -> str:
        if len(candles) < 200:
            return "NORMAL"

        features = calculate_features(candles)

        atr = features.get("atr", 0.0)
        bb_upper = features.get("bb_upper", 0.0)
        bb_lower = features.get("bb_lower", 0.0)
        close = candles[-1].close

        if atr == 0.0 or bb_upper == 0.0 or bb_lower == 0.0:
            return "NORMAL"

        bb_width = (bb_upper - bb_lower) / close
        atr_relative = atr / close

        bb_width_threshold_high = 0.04
        bb_width_threshold_low = 0.02
        atr_threshold_high = 0.015
        atr_threshold_low = 0.005

        if bb_width > bb_width_threshold_high or atr_relative > atr_threshold_high:
            return "HIGH"
        elif bb_width < bb_width_threshold_low and atr_relative < atr_threshold_low:
            return "LOW"
        else:
            return "NORMAL"
