import pandas as pd
import ta

from src.core.models.candle import Candle


def calculate_features(candles: list[Candle]) -> dict[str, float]:
    if len(candles) < 200:
        raise ValueError("Need at least 200 candles to calculate all indicators")

    df = pd.DataFrame(
        {
            "open": [c.open for c in candles],
            "high": [c.high for c in candles],
            "low": [c.low for c in candles],
            "close": [c.close for c in candles],
            "volume": [c.volume for c in candles],
        }
    )

    features: dict[str, float] = {}

    sma_50 = ta.trend.SMAIndicator(close=df["close"], window=50)
    features["sma_50"] = float(sma_50.sma_indicator().iloc[-1])

    sma_200 = ta.trend.SMAIndicator(close=df["close"], window=200)
    features["sma_200"] = float(sma_200.sma_indicator().iloc[-1])

    ema_9 = ta.trend.EMAIndicator(close=df["close"], window=9)
    features["ema_9"] = float(ema_9.ema_indicator().iloc[-1])

    rsi = ta.momentum.RSIIndicator(close=df["close"], window=14)
    features["rsi"] = float(rsi.rsi().iloc[-1])

    bollinger = ta.volatility.BollingerBands(
        close=df["close"], window=20, window_dev=2
    )
    features["bb_upper"] = float(bollinger.bollinger_hband().iloc[-1])
    features["bb_middle"] = float(bollinger.bollinger_mavg().iloc[-1])
    features["bb_lower"] = float(bollinger.bollinger_lband().iloc[-1])

    atr = ta.volatility.AverageTrueRange(
        high=df["high"], low=df["low"], close=df["close"], window=14
    )
    features["atr"] = float(atr.average_true_range().iloc[-1])

    return features
