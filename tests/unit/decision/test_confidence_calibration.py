from __future__ import annotations

from pathlib import Path

import pytest

from src.app.settings import Settings
from src.core.models.technical_analysis import TechnicalAnalysisResult
from src.decision.policy import decide_action
from src.decision.reason_codes import CONFLICT_TREND_STRUCTURE
from src.decision.scoring import DecisionScores

pytestmark = pytest.mark.unit


def _settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.chdir(tmp_path)
    for key in [
        "DECISION_MIN_TRADE_EDGE",
        "DECISION_MAX_NO_TRADE_SCORE",
        "DECISION_MAX_CONFIDENCE_WHEN_NEWS_LOW",
    ]:
        monkeypatch.delenv(key, raising=False)
    return Settings()


def _technical(confidence: float) -> TechnicalAnalysisResult:
    return TechnicalAnalysisResult(
        bias="NEUTRAL",
        confidence=confidence,
        evidence=[],
        contradictions=[],
        setup_type=None,
        no_trade_flags=[],
    )


def test_caps_confidence_when_news_quality_low(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path, monkeypatch)

    scores = DecisionScores(bull_score=100.0, bear_score=0.0, no_trade_score=0.0)
    action, confidence = decide_action(
        scores=scores,
        reason_codes=[],
        settings=settings,
        technical=_technical(0.9),
        news_quality="LOW",
    )

    assert action == "CALL"
    assert confidence == pytest.approx(settings.decision_max_confidence_when_news_low)


def test_downshifts_confidence_on_trend_structure_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path, monkeypatch)

    scores = DecisionScores(bull_score=100.0, bear_score=0.0, no_trade_score=0.0)
    action, confidence = decide_action(
        scores=scores,
        reason_codes=[CONFLICT_TREND_STRUCTURE],
        settings=settings,
        technical=_technical(0.8),
    )

    assert action == "CALL"
    assert confidence == pytest.approx(0.8 * 0.8)


def test_caps_wait_confidence_to_half(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(tmp_path, monkeypatch)

    scores = DecisionScores(bull_score=10.0, bear_score=0.0, no_trade_score=0.0)
    action, confidence = decide_action(
        scores=scores,
        reason_codes=[],
        settings=settings,
        technical=_technical(0.9),
    )

    assert action == "WAIT"
    assert confidence == pytest.approx(0.5)
