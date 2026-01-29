from __future__ import annotations

import pandas as pd
from ta.momentum import RSIIndicator

from src.core.models.candle import Candle


def calculate_momentum_features(candles: list[Candle]) -> dict[str, float]:
    output = {
        "rsi_delta_1": 0.0,
        "rsi_delta_5": 0.0,
        "roc_5": 0.0,
        "roc_20": 0.0,
    }

    if len(candles) < 21:
        return output

    try:
        frame = pd.DataFrame({"close": [candle.close for candle in candles]})
        close = frame["close"].astype(float)

        rsi = RSIIndicator(close=close, window=14).rsi()

        rsi_delta_1 = rsi.diff(1)
        rsi_delta_5 = rsi.diff(5)

        roc_5 = (close / close.shift(5) - 1.0) * 100.0
        roc_20 = (close / close.shift(20) - 1.0) * 100.0

        derived = pd.DataFrame(
            {
                "rsi_delta_1": rsi_delta_1,
                "rsi_delta_5": rsi_delta_5,
                "roc_5": roc_5,
                "roc_20": roc_20,
            }
        )

        derived = derived.replace([float("inf"), float("-inf")], pd.NA).fillna(0.0)
        last_row = derived.iloc[-1]

        return {
            "rsi_delta_1": float(last_row["rsi_delta_1"]),
            "rsi_delta_5": float(last_row["rsi_delta_5"]),
            "roc_5": float(last_row["roc_5"]),
            "roc_20": float(last_row["roc_20"]),
        }
    except Exception:
        return output
