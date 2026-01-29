from __future__ import annotations

import pytest

from src.features.structure.market_structure import classify_structure
from src.features.structure.swing_points import SwingPoint


def test_bullish_hh_hl() -> None:
    swings = [
        SwingPoint(index=1, price=100.0, type="HIGH", timestamp=None),
        SwingPoint(index=2, price=90.0, type="LOW", timestamp=None),
        SwingPoint(index=3, price=110.0, type="HIGH", timestamp=None),
        SwingPoint(index=4, price=95.0, type="LOW", timestamp=None),
    ]

    result = classify_structure(swings)

    assert result["structure"] == "BULLISH"
    assert result["confidence"] == pytest.approx(91.1111111111, rel=1e-6)


def test_bearish_lh_ll() -> None:
    swings = [
        SwingPoint(index=1, price=110.0, type="HIGH", timestamp=None),
        SwingPoint(index=2, price=95.0, type="LOW", timestamp=None),
        SwingPoint(index=3, price=100.0, type="HIGH", timestamp=None),
        SwingPoint(index=4, price=90.0, type="LOW", timestamp=None),
    ]

    result = classify_structure(swings)

    assert result["structure"] == "BEARISH"
    assert result["confidence"] == pytest.approx(88.7081339713, rel=1e-6)


def test_range_mixed_signals() -> None:
    swings = [
        SwingPoint(index=1, price=100.0, type="HIGH", timestamp=None),
        SwingPoint(index=2, price=90.0, type="LOW", timestamp=None),
        SwingPoint(index=3, price=110.0, type="HIGH", timestamp=None),
        SwingPoint(index=4, price=85.0, type="LOW", timestamp=None),
    ]

    result = classify_structure(swings)

    assert result["structure"] == "RANGE"
    assert result["confidence"] == 40.0


def test_insufficient_points_returns_range_zero() -> None:
    swings = [
        SwingPoint(index=1, price=100.0, type="HIGH", timestamp=None),
        SwingPoint(index=2, price=90.0, type="LOW", timestamp=None),
        SwingPoint(index=3, price=95.0, type="LOW", timestamp=None),
    ]

    result = classify_structure(swings)

    assert result == {"structure": "RANGE", "confidence": 0.0}
