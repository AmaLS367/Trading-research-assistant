from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_slope(series: pd.Series, window: int = 10) -> float:
    if window < 2:
        return 0.0

    try:
        values = series.dropna().tail(window).to_numpy(dtype=float)
    except Exception:
        return 0.0

    if values.size < 2:
        return 0.0

    x = np.arange(values.size, dtype=float)
    slope = np.polyfit(x, values, 1)[0]
    return float(slope)


def calculate_normalized_slope(series: pd.Series, window: int = 10) -> float:
    if window < 2:
        return 0.0

    try:
        values = series.dropna().tail(window).to_numpy(dtype=float)
    except Exception:
        return 0.0

    if values.size < 2:
        return 0.0

    last_value = float(values[-1])
    if last_value == 0.0:
        return 0.0

    x = np.arange(values.size, dtype=float)
    slope = float(np.polyfit(x, values, 1)[0])
    normalized = (slope / abs(last_value)) * 100.0
    return float(normalized)
