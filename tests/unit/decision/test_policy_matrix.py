from __future__ import annotations

from pathlib import Path

import pytest

from src.app.settings import Settings
from src.core.models.technical_analysis import TechnicalAnalysisResult
from src.decision.policy import decide_action
from src.decision.reason_codes import build_reason_codes
from src.decision.scoring import calculate_scores

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


def _technical(bias: str, confidence: float) -> TechnicalAnalysisResult:
    return TechnicalAnalysisResult(
        bias=bias,  # type: ignore[arg-type]
        confidence=confidence,
        evidence=[],
        contradictions=[],
        setup_type=None,
        no_trade_flags=[],
    )


@pytest.mark.parametrize(
    ("name", "indicators", "technical", "news_quality", "expected_action"),
    [
        (
            "bullish_edge_call",
            {
                "structure": "BULLISH",
                "dist_sma200_pct": 1.0,
                "ema9_sma50_crossover_type": "BULLISH",
                "ema9_sma50_crossover_age_bars": 2,
                "roc_5": 1.0,
                "rsi_delta_1": 0.2,
                "rsi_delta_5": 0.1,
                "atr_pct": 1.0,
                "bb_squeeze_flag": 1.0,
            },
            _technical("BULLISH", 0.85),
            None,
            "CALL",
        ),
        (
            "bearish_edge_put",
            {
                "structure": "BEARISH",
                "dist_sma200_pct": -1.0,
                "ema9_sma50_crossover_type": "BEARISH",
                "ema9_sma50_crossover_age_bars": 1,
                "roc_5": -1.0,
                "rsi_delta_1": -0.2,
                "rsi_delta_5": -0.1,
                "atr_pct": 1.0,
                "bb_squeeze_flag": 1.0,
            },
            _technical("BEARISH", 0.8),
            None,
            "PUT",
        ),
        (
            "no_trade_volatility_gate_wait",
            {
                "structure": "RANGE",
                "ema9_sma50_crossover_type": "NONE",
                "ema9_sma50_crossover_age_bars": -1,
                "atr_pct": 0.05,
                "bb_squeeze_flag": 0.0,
            },
            _technical("NEUTRAL", 0.9),
            None,
            "WAIT",
        ),
        (
            "weak_edge_wait",
            {
                "dist_sma200_pct": 1.0,
                "atr_pct": 1.0,
                "bb_squeeze_flag": 1.0,
            },
            _technical("NEUTRAL", 0.9),
            None,
            "WAIT",
        ),
        (
            "bullish_edge_call_even_with_low_news",
            {
                "structure": "BULLISH",
                "dist_sma200_pct": 1.0,
                "ema9_sma50_crossover_type": "BULLISH",
                "ema9_sma50_crossover_age_bars": 2,
                "roc_5": 1.0,
                "rsi_delta_1": 0.2,
                "rsi_delta_5": 0.1,
                "atr_pct": 1.0,
                "bb_squeeze_flag": 1.0,
            },
            _technical("BULLISH", 0.9),
            "LOW",
            "CALL",
        ),
    ],
)
def test_policy_matrix_decides_expected_action(
    name: str,
    indicators: dict[str, object],
    technical: TechnicalAnalysisResult,
    news_quality: str | None,
    expected_action: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = name
    settings = _settings(tmp_path, monkeypatch)

    technical_scoring_dict: dict[str, object] = {
        "trend_direction": technical.bias,
        "trend_strength": float(technical.confidence) * 100.0,
    }
    scores = calculate_scores(indicators, technical_analysis=technical_scoring_dict)
    reason_codes = build_reason_codes(indicators, scores=scores)

    action, _ = decide_action(
        scores=scores,
        reason_codes=reason_codes,
        settings=settings,
        technical=technical,
        news_quality=news_quality,
    )

    assert action == expected_action


def test_policy_matrix_wait_confidence_is_capped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path, monkeypatch)

    indicators: dict[str, object] = {
        "dist_sma200_pct": 1.0,
        "atr_pct": 1.0,
        "bb_squeeze_flag": 1.0,
    }
    technical = _technical("NEUTRAL", 0.9)
    technical_scoring_dict: dict[str, object] = {
        "trend_direction": technical.bias,
        "trend_strength": float(technical.confidence) * 100.0,
    }
    scores = calculate_scores(indicators, technical_analysis=technical_scoring_dict)
    reason_codes = build_reason_codes(indicators, scores=scores)

    action, confidence = decide_action(
        scores=scores,
        reason_codes=reason_codes,
        settings=settings,
        technical=technical,
    )

    assert action == "WAIT"
    assert 0.0 <= confidence <= 0.5
