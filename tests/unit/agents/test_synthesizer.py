import json
from datetime import datetime
from unittest.mock import Mock

from src.agents.synthesizer import Synthesizer
from src.core.models.news import NewsDigest
from src.core.models.timeframe import Timeframe
from src.core.ports.llm_provider import LlmProvider


def test_synthesizer_creates_recommendation() -> None:
    mock_llm = Mock(spec=LlmProvider)
    mock_response = json.dumps(
        {
            "action": "CALL",
            "confidence": 0.75,
            "brief": "Strong bullish momentum with RSI above 70.",
        }
    )
    mock_llm.generate.return_value = mock_response

    synthesizer = Synthesizer(mock_llm)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug = synthesizer.synthesize(
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
    mock_llm = Mock(spec=LlmProvider)
    mock_response = (
        "```json\n"
        + json.dumps({"action": "PUT", "confidence": 0.6, "brief": "Bearish trend detected."})
        + "\n```"
    )
    mock_llm.generate.return_value = mock_response

    synthesizer = Synthesizer(mock_llm)

    news_digest = NewsDigest(
        symbol="GBPUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug = synthesizer.synthesize(
        symbol="GBPUSD",
        timeframe=Timeframe.H1,
        technical_view="Price below SMA 200.",
        news_digest=news_digest,
    )

    assert recommendation.action == "PUT"
    assert recommendation.confidence == 0.6
    assert debug["parse_ok"] is True


def test_synthesizer_validates_action() -> None:
    mock_llm = Mock(spec=LlmProvider)
    mock_response = json.dumps({"action": "INVALID", "confidence": 0.5, "brief": "Test"})
    mock_llm.generate.return_value = mock_response

    synthesizer = Synthesizer(mock_llm)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view="Test",
        news_digest=news_digest,
    )

    assert recommendation.action == "WAIT"
    assert recommendation.confidence == 0.0
    assert "LLM JSON parse error" in recommendation.brief or debug["parse_error"] is not None


def test_synthesizer_validates_confidence_range() -> None:
    mock_llm = Mock(spec=LlmProvider)
    mock_response = json.dumps({"action": "WAIT", "confidence": 1.5, "brief": "Test"})
    mock_llm.generate.return_value = mock_response

    synthesizer = Synthesizer(mock_llm)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view="Test",
        news_digest=news_digest,
    )

    assert recommendation.action == "WAIT"
    assert recommendation.confidence == 0.0
    assert "LLM JSON parse error" in recommendation.brief or debug["parse_error"] is not None


def test_synthesizer_handles_missing_fields() -> None:
    mock_llm = Mock(spec=LlmProvider)
    mock_response = json.dumps({"action": "CALL", "confidence": 0.8})
    mock_llm.generate.return_value = mock_response

    synthesizer = Synthesizer(mock_llm)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view="Test",
        news_digest=news_digest,
    )

    assert recommendation.action == "WAIT"
    assert recommendation.confidence == 0.0
    assert "LLM JSON parse error" in recommendation.brief or debug["parse_error"] is not None


def test_synthesizer_handles_invalid_json_with_fallback() -> None:
    mock_llm = Mock(spec=LlmProvider)
    mock_llm.generate.return_value = "This is not JSON"

    synthesizer = Synthesizer(mock_llm)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug = synthesizer.synthesize(
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


def test_synthesizer_handles_invalid_json_retry_also_fails() -> None:
    mock_llm = Mock(spec=LlmProvider)
    mock_llm.generate.side_effect = ["This is not JSON", "Also not JSON", "Still not JSON"]

    synthesizer = Synthesizer(mock_llm)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug = synthesizer.synthesize(
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
    mock_llm = Mock(spec=LlmProvider)
    mock_response = json.dumps(
        {"action": "CALL", "confidence": 0.8, "brief": "First line.\nSecond line.\nThird line."}
    )
    mock_llm.generate.return_value = mock_response

    synthesizer = Synthesizer(mock_llm)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view="Test",
        news_digest=news_digest,
    )

    assert recommendation.brief == "First line. Second line. Third line."
    assert "\n" not in recommendation.brief
    assert debug["parse_ok"] is True


def test_synthesizer_warns_on_curly_braces_in_brief() -> None:
    mock_llm = Mock(spec=LlmProvider)
    mock_response = json.dumps(
        {"action": "PUT", "confidence": 0.7, "brief": "Analysis shows {some data} in the market."}
    )
    mock_llm.generate.return_value = mock_response

    synthesizer = Synthesizer(mock_llm)

    news_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="MEDIUM",
        quality_reason="Test",
    )

    recommendation, debug = synthesizer.synthesize(
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
