from __future__ import annotations

import json
from unittest.mock import Mock

import pytest

from src.agents.synthesizer import Synthesizer
from src.core.models.llm import LlmResponse
from src.core.models.news import NewsDigest
from src.core.models.timeframe import Timeframe
from src.llm.providers.llm_router import LlmRouter

pytestmark = pytest.mark.unit


def _technical_view_json(confidence: float, bias: str = "NEUTRAL") -> str:
    return json.dumps(
        {
            "bias": bias,
            "confidence": confidence,
            "evidence": [],
            "contradictions": [],
            "setup_type": None,
            "no_trade_flags": [],
        }
    )


def _news_digest() -> NewsDigest:
    return NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )


def test_synthesizer_forces_call_when_bull_edge_is_high(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
    mock_router = Mock(spec=LlmRouter)
    mock_router.generate.return_value = LlmResponse(
        text=json.dumps({"action": "PUT", "confidence": 0.1, "brief": "Explanation text."}),
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=10,
        attempts=1,
        error=None,
    )

    synthesizer = Synthesizer(mock_router)

    indicators: dict[str, object] = {
        "trend_direction": "BULLISH",
        "trend_strength": 80.0,
        "structure": "BULLISH",
        "dist_sma200_pct": 1.0,
        "ema9_sma50_crossover_type": "BULLISH",
        "ema9_sma50_crossover_age_bars": 2,
        "roc_5": 1.0,
        "rsi_delta_1": 0.2,
        "rsi_delta_5": 0.1,
        "atr_pct": 1.0,
        "bb_squeeze_flag": 1.0,
    }

    recommendation, debug, _ = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view=_technical_view_json(confidence=0.9, bias="BULLISH"),
        news_digest=_news_digest(),
        indicators=indicators,
    )

    assert recommendation.action == "CALL"
    assert recommendation.confidence == pytest.approx(0.9)
    assert debug["decision"]["action"] == "CALL"


def test_synthesizer_forces_put_when_bear_edge_is_high(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
    mock_router = Mock(spec=LlmRouter)
    mock_router.generate.return_value = LlmResponse(
        text=json.dumps({"action": "CALL", "confidence": 0.9, "brief": "Explanation text."}),
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=10,
        attempts=1,
        error=None,
    )

    synthesizer = Synthesizer(mock_router)

    indicators: dict[str, object] = {
        "trend_direction": "BEARISH",
        "trend_strength": 80.0,
        "structure": "BEARISH",
        "dist_sma200_pct": -1.0,
        "ema9_sma50_crossover_type": "BEARISH",
        "ema9_sma50_crossover_age_bars": 1,
        "roc_5": -1.0,
        "rsi_delta_1": -0.2,
        "rsi_delta_5": -0.1,
        "atr_pct": 1.0,
        "bb_squeeze_flag": 1.0,
    }

    recommendation, debug, _ = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view=_technical_view_json(confidence=0.8, bias="BEARISH"),
        news_digest=_news_digest(),
        indicators=indicators,
    )

    assert recommendation.action == "PUT"
    assert recommendation.confidence == pytest.approx(0.8)
    assert debug["decision"]["action"] == "PUT"


def test_synthesizer_forces_wait_when_no_trade_score_exceeds_threshold(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
    mock_router = Mock(spec=LlmRouter)
    mock_router.generate.return_value = LlmResponse(
        text=json.dumps({"action": "CALL", "confidence": 1.0, "brief": "Explanation text."}),
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=10,
        attempts=1,
        error=None,
    )

    synthesizer = Synthesizer(mock_router)

    indicators: dict[str, object] = {
        "trend_direction": "NEUTRAL",
        "structure": "RANGE",
        "ema9_sma50_crossover_type": "NONE",
        "atr_pct": 0.05,
        "bb_squeeze_flag": 0.0,
    }

    recommendation, debug, _ = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view=_technical_view_json(confidence=0.9, bias="NEUTRAL"),
        news_digest=_news_digest(),
        indicators=indicators,
    )

    assert recommendation.action == "WAIT"
    assert recommendation.confidence == pytest.approx(0.4)
    assert debug["decision"]["action"] == "WAIT"
