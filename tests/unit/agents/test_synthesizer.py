import json
from datetime import datetime
from unittest.mock import Mock

from src.agents.synthesizer import Synthesizer
from src.core.models.llm import LlmResponse
from src.core.models.news import NewsDigest
from src.core.models.timeframe import Timeframe
from src.llm.providers.llm_router import LlmRouter


def test_synthesizer_creates_recommendation() -> None:
    mock_router = Mock(spec=LlmRouter)
    mock_response_text = json.dumps(
        {
            "action": "CALL",
            "confidence": 0.75,
            "brief": "Strong bullish momentum with RSI above 70.",
        }
    )
    mock_router.generate.return_value = LlmResponse(
        text=mock_response_text,
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )

    synthesizer = Synthesizer(mock_router)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug, llm_response = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view="RSI is 75, indicating overbought conditions.",
        news_digest=news_digest,
    )

    assert recommendation.symbol == "EURUSD"
    assert recommendation.timeframe == Timeframe.H1
    assert recommendation.action == "CALL"
    assert recommendation.confidence == 0.75
    assert recommendation.brief == "Strong bullish momentum with RSI above 70."
    assert isinstance(recommendation.timestamp, datetime)
    assert debug["parse_ok"] is True


def test_synthesizer_handles_json_with_code_blocks() -> None:
    mock_router = Mock(spec=LlmRouter)
    mock_response_text = (
        "```json\n"
        + json.dumps({"action": "PUT", "confidence": 0.6, "brief": "Bearish trend detected."})
        + "\n```"
    )
    mock_router.generate.return_value = LlmResponse(
        text=mock_response_text,
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )

    synthesizer = Synthesizer(mock_router)

    news_digest = NewsDigest(
        symbol="GBPUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug, llm_response = synthesizer.synthesize(
        symbol="GBPUSD",
        timeframe=Timeframe.H1,
        technical_view="Price below SMA 200.",
        news_digest=news_digest,
    )

    assert recommendation.action == "PUT"
    assert recommendation.confidence == 0.6
    assert debug["parse_ok"] is True


def test_synthesizer_validates_action() -> None:
    mock_router = Mock(spec=LlmRouter)
    mock_response_text = json.dumps({"action": "INVALID", "confidence": 0.5, "brief": "Test"})
    mock_router.generate.return_value = LlmResponse(
        text=mock_response_text,
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )

    synthesizer = Synthesizer(mock_router)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug, llm_response = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view="Test",
        news_digest=news_digest,
    )

    assert recommendation.action == "WAIT"
    assert recommendation.confidence == 0.0
    assert "LLM JSON parse error" in recommendation.brief or debug["parse_error"] is not None


def test_synthesizer_validates_confidence_range() -> None:
    mock_router = Mock(spec=LlmRouter)
    mock_response_text = json.dumps({"action": "WAIT", "confidence": 1.5, "brief": "Test"})
    mock_router.generate.return_value = LlmResponse(
        text=mock_response_text,
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )

    synthesizer = Synthesizer(mock_router)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug, llm_response = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view="Test",
        news_digest=news_digest,
    )

    assert recommendation.action == "WAIT"
    assert recommendation.confidence == 0.0
    assert "LLM JSON parse error" in recommendation.brief or debug["parse_error"] is not None


def test_synthesizer_handles_missing_fields() -> None:
    mock_router = Mock(spec=LlmRouter)
    mock_response_text = json.dumps({"action": "CALL", "confidence": 0.8})
    mock_router.generate.return_value = LlmResponse(
        text=mock_response_text,
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )

    synthesizer = Synthesizer(mock_router)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug, llm_response = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view="Test",
        news_digest=news_digest,
    )

    assert recommendation.action == "WAIT"
    assert recommendation.confidence == 0.0
    assert "LLM JSON parse error" in recommendation.brief or debug["parse_error"] is not None


def test_synthesizer_handles_invalid_json_with_fallback() -> None:
    mock_router = Mock(spec=LlmRouter)
    mock_router.generate.side_effect = [
        LlmResponse(
            text="This is not JSON",
            provider_name="test_provider",
            model_name="test_model",
            latency_ms=100,
            attempts=1,
            error=None,
        ),
        LlmResponse(
            text=json.dumps({"action": "WAIT", "confidence": 0.0, "brief": "Fallback"}),
            provider_name="test_provider",
            model_name="test_model",
            latency_ms=100,
            attempts=1,
            error=None,
        ),
    ]

    synthesizer = Synthesizer(mock_router)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug, llm_response = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view="Test",
        news_digest=news_digest,
    )

    assert recommendation.action == "WAIT"
    assert recommendation.confidence == 0.0
    assert "Fallback" in recommendation.brief or "LLM JSON parse error" in recommendation.brief
    assert debug["retry_used"] is True


def test_synthesizer_handles_invalid_json_retry_also_fails() -> None:
    mock_router = Mock(spec=LlmRouter)
    mock_router.generate.side_effect = [
        LlmResponse(
            text="This is not JSON",
            provider_name="test_provider",
            model_name="test_model",
            latency_ms=100,
            attempts=1,
            error=None,
        ),
        LlmResponse(
            text="Also not JSON",
            provider_name="test_provider",
            model_name="test_model",
            latency_ms=100,
            attempts=1,
            error=None,
        ),
        LlmResponse(
            text="Still not JSON",
            provider_name="test_provider",
            model_name="test_model",
            latency_ms=100,
            attempts=1,
            error=None,
        ),
    ]

    synthesizer = Synthesizer(mock_router)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug, llm_response = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view="Test",
        news_digest=news_digest,
    )

    assert recommendation.action == "WAIT"
    assert recommendation.confidence == 0.0
    assert "LLM JSON parse error" in recommendation.brief
    assert debug["parse_ok"] is False
    assert debug["parse_error"] is not None
    assert debug["retry_used"] is True
    assert debug["retry_raw_output"] is not None


def test_synthesizer_normalizes_brief_newlines() -> None:
    mock_router = Mock(spec=LlmRouter)
    mock_response_text = json.dumps(
        {"action": "CALL", "confidence": 0.8, "brief": "First line.\nSecond line.\nThird line."}
    )
    mock_router.generate.return_value = LlmResponse(
        text=mock_response_text,
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )

    synthesizer = Synthesizer(mock_router)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug, llm_response = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view="Test",
        news_digest=news_digest,
    )

    assert recommendation.brief == "First line. Second line. Third line."
    assert "\n" not in recommendation.brief
    assert debug["parse_ok"] is True


def test_synthesizer_warns_on_curly_braces_in_brief() -> None:
    mock_router = Mock(spec=LlmRouter)
    mock_response_text = json.dumps(
        {"action": "PUT", "confidence": 0.7, "brief": "Analysis shows {some data} in the market."}
    )
    mock_router.generate.return_value = LlmResponse(
        text=mock_response_text,
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )

    synthesizer = Synthesizer(mock_router)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug, llm_response = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view="Test",
        news_digest=news_digest,
    )

    assert recommendation.action == "PUT"
    assert recommendation.confidence == 0.7
    assert "{" in recommendation.brief or "}" in recommendation.brief
    assert debug["parse_ok"] is True
    assert debug["brief_warning"] == "Brief contains curly braces (possible nested JSON)"
