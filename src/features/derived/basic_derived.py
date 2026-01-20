from __future__ import annotations

import pandas as pd

from src.core.models.candle import Candle


def calculate_basic_derived(candles: list[Candle]) -> dict[str, float]:
    keys = [
        "price_change_pct_1",
        "price_change_pct_5",
        "price_change_pct_20",
        "range_pct",
        "body_pct",
    ]

    if not candles:
        return dict.fromkeys(keys, 0.0)

    frame = pd.DataFrame(
        {
            "open": [candle.open for candle in candles],
            "high": [candle.high for candle in candles],
            "low": [candle.low for candle in candles],
            "close": [candle.close for candle in candles],
            "volume": [candle.volume for candle in candles],
        }
    )

    close = frame["close"].astype(float)
    open_price = frame["open"].astype(float)
    high = frame["high"].astype(float)
    low = frame["low"].astype(float)

    derived = pd.DataFrame(index=frame.index)

    derived["price_change_pct_1"] = (close / close.shift(1) - 1.0) * 100.0
    derived["price_change_pct_5"] = (close / close.shift(5) - 1.0) * 100.0
    derived["price_change_pct_20"] = (close / close.shift(20) - 1.0) * 100.0

    derived["range_pct"] = ((high - low) / close) * 100.0
    derived["body_pct"] = ((open_price - close).abs() / close) * 100.0

    derived = derived.replace([float("inf"), float("-inf")], pd.NA).fillna(0.0)

    last_row = derived.iloc[-1]
    return {key: float(last_row[key]) for key in keys}
