from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.core.models.candle import Candle


def calculate_volume_features(candles: list[Candle], window: int = 20) -> dict[str, object]:
    output: dict[str, object] = {
        "volume_mean": 0.0,
        "volume_zscore": 0.0,
        "volume_trend": "UNKNOWN",
        "volume_confirmation_flag": 0.0,
    }

    if not candles:
        return output

    volumes: list[float] = []
    for candle in candles:
        if not hasattr(candle, "volume"):
            volumes.append(float("nan"))
            continue

        try:
            volumes.append(float(candle.volume))
        except Exception:
            volumes.append(float("nan"))

    series = pd.Series(volumes, dtype=float)
    non_nan = series.dropna()

    if non_nan.empty:
        return output

    if (non_nan == 0.0).all():
        return output

    if window < 1:
        window = 1

    rolling_mean = series.rolling(window=window, min_periods=window).mean()
    mean_last = rolling_mean.iloc[-1]
    if pd.isna(mean_last):
        mean_value = float(non_nan.mean())
    else:
        mean_value = float(mean_last)

    if not math.isfinite(mean_value):
        mean_value = 0.0

    last_volume = series.iloc[-1]
    if pd.isna(last_volume):
        last_volume_value = 0.0
    else:
        last_volume_value = float(last_volume)

    rolling_std = series.rolling(window=window, min_periods=window).std(ddof=0)
    std_last = rolling_std.iloc[-1]
    if pd.isna(std_last):
        std_value = float(non_nan.std(ddof=0))
    else:
        std_value = float(std_last)

    if not math.isfinite(std_value) or std_value == 0.0:
        zscore = 0.0
    else:
        zscore = (last_volume_value - mean_value) / std_value
        if not math.isfinite(zscore):
            zscore = 0.0

    last_10 = series.tail(10)
    if len(last_10) == 10 and last_10.notna().all():
        prev5 = float(last_10.iloc[:5].mean())
        last5 = float(last_10.iloc[5:].mean())

        if math.isfinite(prev5) and math.isfinite(last5):
            if prev5 == 0.0:
                if last5 == 0.0:
                    trend = "FLAT"
                else:
                    trend = "RISING"
            else:
                change_ratio = (last5 - prev5) / abs(prev5)
                if change_ratio >= 0.05:
                    trend = "RISING"
                elif change_ratio <= -0.05:
                    trend = "FALLING"
                else:
                    trend = "FLAT"
        else:
            trend = "UNKNOWN"
    else:
        trend = "UNKNOWN"

    confirmation_flag = 1.0 if zscore >= 1.0 else 0.0

    output["volume_mean"] = float(mean_value)
    output["volume_zscore"] = float(zscore)
    output["volume_trend"] = trend
    output["volume_confirmation_flag"] = float(confirmation_flag)

    return output
