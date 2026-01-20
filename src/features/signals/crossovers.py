from __future__ import annotations

import numpy as np
import pandas as pd

from src.core.models.candle import Candle


def _detect_last_crossover(
    a: pd.Series,
    b: pd.Series,
    lookback_bars: int,
    bullish_type: str,
    bearish_type: str,
) -> tuple[str, int]:
    if lookback_bars < 1:
        return "NONE", -1

    diff = a - b
    last_valid_index = diff.last_valid_index()
    if last_valid_index is None:
        return "NONE", -1

    try:
        last_valid_index_int = int(last_valid_index)
    except Exception:
        return "NONE", -1

    start_index = max(0, last_valid_index_int - lookback_bars + 1)
    window = diff.loc[start_index:last_valid_index_int]
    if window.empty:
        return "NONE", -1

    sign = pd.Series(np.sign(window.to_numpy(dtype=float)), index=window.index)
    sign_clean = sign.replace(0.0, pd.NA).ffill()
    prev_sign = sign_clean.shift(1)

    bullish = (prev_sign < 0.0) & (sign_clean > 0.0)
    bearish = (prev_sign > 0.0) & (sign_clean < 0.0)

    bullish_indices = bullish[bullish].index
    bearish_indices = bearish[bearish].index

    last_bullish_index = int(bullish_indices.max()) if len(bullish_indices) > 0 else None
    last_bearish_index = int(bearish_indices.max()) if len(bearish_indices) > 0 else None

    if last_bullish_index is None and last_bearish_index is None:
        return "NONE", -1

    if last_bearish_index is None or (
        last_bullish_index is not None and last_bullish_index > last_bearish_index
    ):
        crossover_type = bullish_type
        crossover_index = last_bullish_index
    else:
        crossover_type = bearish_type
        crossover_index = last_bearish_index

    age_bars = last_valid_index_int - int(crossover_index)
    return crossover_type, int(age_bars)


def detect_crossovers(candles: list[Candle], lookback_bars: int = 50) -> dict[str, object]:
    result = {
        "ema9_sma50_crossover_type": "NONE",
        "ema9_sma50_crossover_age_bars": -1,
        "sma50_sma200_crossover_type": "NONE",
        "sma50_sma200_crossover_age_bars": -1,
    }

    if not candles:
        return result

    try:
        close = pd.Series([candle.close for candle in candles], dtype=float)
    except Exception:
        return result

    ema_9 = close.ewm(span=9, adjust=False).mean()
    sma_50 = close.rolling(window=50).mean()
    sma_200 = close.rolling(window=200).mean()

    if sma_50.dropna().empty:
        return result

    ema9_type, ema9_age = _detect_last_crossover(
        a=ema_9,
        b=sma_50,
        lookback_bars=lookback_bars,
        bullish_type="BULLISH",
        bearish_type="BEARISH",
    )
    result["ema9_sma50_crossover_type"] = ema9_type
    result["ema9_sma50_crossover_age_bars"] = ema9_age

    if sma_200.dropna().empty:
        return result

    sma_type, sma_age = _detect_last_crossover(
        a=sma_50,
        b=sma_200,
        lookback_bars=lookback_bars,
        bullish_type="GOLDEN",
        bearish_type="DEATH",
    )
    result["sma50_sma200_crossover_type"] = sma_type
    result["sma50_sma200_crossover_age_bars"] = sma_age

    return result
