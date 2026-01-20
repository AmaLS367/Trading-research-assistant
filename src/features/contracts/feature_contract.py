from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.core.models.candle import Candle


class ValidationStatus(str, Enum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    INVALID = "INVALID"


@dataclass
class ValidationResult:
    status: ValidationStatus
    reasons: list[str]
    candle_count: int


class FeatureContract:
    @staticmethod
    def validate(candles: list[Candle], min_count: int = 200) -> ValidationResult:
        candle_count = len(candles)
        invalid_reasons: list[str] = []
        degraded_reasons: list[str] = []

        if candle_count < min_count:
            invalid_reasons.append(
                f"insufficient_candles: expected>={min_count} got={candle_count}"
            )

        if candle_count == 0:
            if invalid_reasons:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    reasons=invalid_reasons,
                    candle_count=candle_count,
                )

            invalid_reasons.append("no_candles")
            return ValidationResult(
                status=ValidationStatus.INVALID,
                reasons=invalid_reasons,
                candle_count=candle_count,
            )

        has_non_positive_prices = False
        has_high_less_than_low = False
        has_open_outside_range = False
        has_close_outside_range = False

        for candle in candles:
            try:
                open_price = float(candle.open)
                high_price = float(candle.high)
                low_price = float(candle.low)
                close_price = float(candle.close)
            except Exception:
                has_non_positive_prices = True
                continue

            if open_price <= 0.0 or high_price <= 0.0 or low_price <= 0.0 or close_price <= 0.0:
                has_non_positive_prices = True

            if high_price < low_price:
                has_high_less_than_low = True

            if open_price < low_price or open_price > high_price:
                has_open_outside_range = True

            if close_price < low_price or close_price > high_price:
                has_close_outside_range = True

        if has_non_positive_prices:
            invalid_reasons.append("non_positive_prices")
        if has_high_less_than_low:
            invalid_reasons.append("high_less_than_low")
        if has_open_outside_range:
            invalid_reasons.append("open_outside_range")
        if has_close_outside_range:
            invalid_reasons.append("close_outside_range")

        timestamps: list[datetime] = []
        has_timestamp_attr = True
        for candle in candles:
            if not hasattr(candle, "timestamp"):
                has_timestamp_attr = False
                break
            timestamps.append(candle.timestamp)

        if has_timestamp_attr and timestamps:
            has_non_monotonic_timestamps = False
            for idx in range(1, len(timestamps)):
                if timestamps[idx] < timestamps[idx - 1]:
                    has_non_monotonic_timestamps = True
                    break

            if has_non_monotonic_timestamps:
                invalid_reasons.append("timestamps_not_monotonic_non_decreasing")
            else:
                if len(set(timestamps)) < len(timestamps):
                    degraded_reasons.append("duplicate_timestamps")

                positive_deltas_seconds: list[float] = []
                for idx in range(1, len(timestamps)):
                    delta_seconds = (timestamps[idx] - timestamps[idx - 1]).total_seconds()
                    if delta_seconds > 0.0:
                        positive_deltas_seconds.append(delta_seconds)

                if positive_deltas_seconds:
                    expected_step_seconds = min(positive_deltas_seconds)
                    if expected_step_seconds > 0.0:
                        has_gaps = False
                        for delta_seconds in positive_deltas_seconds:
                            if delta_seconds > expected_step_seconds * 1.5:
                                has_gaps = True
                                break
                        if has_gaps:
                            degraded_reasons.append("timestamp_gaps_detected")

        if not all(hasattr(candle, "volume") for candle in candles):
            degraded_reasons.append("volume_missing_or_all_zero")
        else:
            all_zero_volume = True
            for candle in candles:
                try:
                    volume = float(candle.volume)
                except Exception:
                    volume = 0.0
                if volume != 0.0:
                    all_zero_volume = False
                    break
            if all_zero_volume:
                degraded_reasons.append("volume_missing_or_all_zero")

        if invalid_reasons:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                reasons=invalid_reasons,
                candle_count=candle_count,
            )

        if degraded_reasons:
            return ValidationResult(
                status=ValidationStatus.DEGRADED,
                reasons=degraded_reasons,
                candle_count=candle_count,
            )

        return ValidationResult(
            status=ValidationStatus.OK,
            reasons=[],
            candle_count=candle_count,
        )
