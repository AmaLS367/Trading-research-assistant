from __future__ import annotations

import pandas as pd
import pytest

from src.features.math.slope import calculate_normalized_slope, calculate_slope


def test_calculate_slope_rising_series() -> None:
    series = pd.Series([1, 2, 3, 4, 5])

    slope = calculate_slope(series, window=5)

    assert slope == pytest.approx(1.0)


def test_calculate_slope_flat_series() -> None:
    series = pd.Series([5, 5, 5, 5, 5])

    slope = calculate_slope(series, window=5)

    assert slope == pytest.approx(0.0)


def test_calculate_slope_short_series() -> None:
    series = pd.Series([1])

    slope = calculate_slope(series, window=10)

    assert slope == pytest.approx(0.0)


def test_calculate_normalized_slope_rising_positive() -> None:
    series = pd.Series([1, 2, 3, 4, 5])

    normalized = calculate_normalized_slope(series, window=5)

    assert normalized > 0.0


def test_calculate_normalized_slope_flat_zero() -> None:
    series = pd.Series([5, 5, 5, 5, 5])

    normalized = calculate_normalized_slope(series, window=5)

    assert normalized == pytest.approx(0.0)
