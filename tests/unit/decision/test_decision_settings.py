from __future__ import annotations

from pathlib import Path

import pytest

from src.app.settings import Settings

pytestmark = pytest.mark.unit


def test_decision_settings_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    for key in [
        "DECISION_MIN_TRADE_EDGE",
        "DECISION_MAX_NO_TRADE_SCORE",
        "DECISION_CROSSOVER_MAX_AGE_BARS",
        "DECISION_ATR_PCT_LOW_THRESHOLD",
        "DECISION_MAX_CONFIDENCE_WHEN_NEWS_LOW",
    ]:
        monkeypatch.delenv(key, raising=False)

    settings = Settings()

    assert settings.decision_min_trade_edge == 15.0
    assert settings.decision_max_no_trade_score == 40.0
    assert settings.decision_crossover_max_age_bars == 10
    assert settings.decision_atr_pct_low_threshold == 0.08
    assert settings.decision_max_confidence_when_news_low == 0.65


def test_decision_settings_load_from_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DECISION_MIN_TRADE_EDGE", "22.5")
    monkeypatch.setenv("DECISION_MAX_NO_TRADE_SCORE", "33.0")
    monkeypatch.setenv("DECISION_CROSSOVER_MAX_AGE_BARS", "7")
    monkeypatch.setenv("DECISION_ATR_PCT_LOW_THRESHOLD", "0.09")
    monkeypatch.setenv("DECISION_MAX_CONFIDENCE_WHEN_NEWS_LOW", "0.5")

    settings = Settings()

    assert settings.decision_min_trade_edge == 22.5
    assert settings.decision_max_no_trade_score == 33.0
    assert settings.decision_crossover_max_age_bars == 7
    assert settings.decision_atr_pct_low_threshold == 0.09
    assert settings.decision_max_confidence_when_news_low == 0.5
