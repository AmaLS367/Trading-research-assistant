from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.core.models.candle import Candle

SwingPointType = Literal["HIGH", "LOW"]


@dataclass(frozen=True)
class SwingPoint:
    index: int
    price: float
    type: SwingPointType
    timestamp: object | None


def detect_swings(candles: list[Candle], depth: int = 5) -> list[SwingPoint]:
    if depth < 1:
        return []

    if len(candles) < (2 * depth + 1):
        return []

    swings: list[SwingPoint] = []

    try:
        last_confirmed_index_exclusive = len(candles) - depth
        for i in range(depth, last_confirmed_index_exclusive):
            center = candles[i]
            center_high = float(center.high)
            center_low = float(center.low)

            left = i - depth
            right_exclusive = i + depth + 1

            is_swing_high = True
            is_swing_low = True

            for j in range(left, right_exclusive):
                if j == i:
                    continue

                other = candles[j]
                if center_high <= float(other.high):
                    is_swing_high = False
                if center_low >= float(other.low):
                    is_swing_low = False

                if not is_swing_high and not is_swing_low:
                    break

            timestamp = center.timestamp if hasattr(center, "timestamp") else None

            if is_swing_high:
                swings.append(
                    SwingPoint(
                        index=i,
                        price=center_high,
                        type="HIGH",
                        timestamp=timestamp,
                    )
                )

            if is_swing_low:
                swings.append(
                    SwingPoint(
                        index=i,
                        price=center_low,
                        type="LOW",
                        timestamp=timestamp,
                    )
                )

        swings.sort(key=lambda sp: sp.index)
        return swings
    except Exception:
        return []
