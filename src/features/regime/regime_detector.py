from src.core.models.candle import Candle
from src.features.indicators.indicator_engine import calculate_features


class RegimeDetector:
    @staticmethod
    def detect(candles: list[Candle]) -> str:
        if len(candles) < 200:
            return "RANGE"

        features = calculate_features(candles)
        current_price = candles[-1].close

        sma_50 = features.get("sma_50", 0.0)
        sma_200 = features.get("sma_200", 0.0)

        if sma_50 == 0.0 or sma_200 == 0.0:
            return "RANGE"

        price_above_sma50 = current_price > sma_50
        price_above_sma200 = current_price > sma_200
        sma50_above_sma200 = sma_50 > sma_200

        if price_above_sma50 and price_above_sma200 and sma50_above_sma200:
            return "BULL_TREND"
        elif not price_above_sma50 and not price_above_sma200 and not sma50_above_sma200:
            return "BEAR_TREND"
        else:
            return "RANGE"
