from __future__ import annotations

from datetime import datetime

from src.core.models.candle import Candle
from src.features.snapshots.feature_snapshot import FeatureSnapshot


def test_feature_snapshot_markdown_contains_sections_and_no_crash_with_none_fields() -> None:
    candle = Candle(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        open=1.0,
        high=1.1,
        low=0.9,
        close=1.0,
        volume=0.0,
    )

    snapshot = FeatureSnapshot(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        candles=[candle],
        indicators={
            "rsi": 50.0,
            "sma_50": 1.0,
            "sma_200": 1.0,
            "ema_9": 1.0,
            "bb_upper": 1.1,
            "bb_middle": 1.0,
            "bb_lower": 0.9,
            "atr": 0.01,
        },
        trend_direction=None,
        trend_strength=None,
        ema9_sma50_crossover_type=None,
        ema9_sma50_crossover_age_bars=None,
        sma50_sma200_crossover_type=None,
        sma50_sma200_crossover_age_bars=None,
        candlestick_pattern=None,
        candlestick_pattern_strength=None,
        volume_trend=None,
    )

    markdown = snapshot.to_markdown()

    assert "### Trend" in markdown
    assert "### Structure" in markdown
    assert "### Momentum" in markdown
    assert "### Crossovers" in markdown
    assert "### Volatility/BB" in markdown
    assert "### Volume" in markdown
    assert "### Patterns" in markdown

    assert "N/A" in markdown
