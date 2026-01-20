from __future__ import annotations

import pytest

from src.core.services.reporter import count_reason_codes

pytestmark = pytest.mark.unit


def test_count_reason_codes_handles_json_and_ignores_invalid() -> None:
    values: list[object] = [
        '["LOW_VOLATILITY_NO_SQUEEZE","NO_FRESH_CROSSOVER"]',
        '["NO_FRESH_CROSSOVER"]',
        "not json",
        None,
        ["weak_momentum"],
        '[""]',
    ]

    counts = count_reason_codes(values)

    assert counts["LOW_VOLATILITY_NO_SQUEEZE"] == 1
    assert counts["NO_FRESH_CROSSOVER"] == 2
    assert counts["WEAK_MOMENTUM"] == 1
