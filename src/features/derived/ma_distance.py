from __future__ import annotations


def calculate_ma_distances(
    close_price: float,
    indicators: dict[str, float],
) -> dict[str, float]:
    def safe_distance(ma_key: str) -> float:
        ma_value = indicators.get(ma_key)
        if ma_value is None:
            return 0.0

        try:
            ma_float = float(ma_value)
            close_float = float(close_price)
        except Exception:
            return 0.0

        if ma_float == 0.0:
            return 0.0

        return ((close_float - ma_float) / ma_float) * 100.0

    return {
        "dist_sma50_pct": float(safe_distance("sma_50")),
        "dist_sma200_pct": float(safe_distance("sma_200")),
        "dist_ema9_pct": float(safe_distance("ema_9")),
    }
