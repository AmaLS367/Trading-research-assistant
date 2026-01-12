import json
from datetime import datetime
from unittest.mock import Mock

import pytest

from src.agents.synthesizer import Synthesizer
from src.core.models.timeframe import Timeframe
from src.core.ports.llm_provider import LlmProvider


def test_synthesizer_creates_recommendation() -> None:
    mock_llm = Mock(spec=LlmProvider)
    mock_response = json.dumps({
        "action": "CALL",
        "confidence": 0.75,
        "brief": "Strong bullish momentum with RSI above 70."
    })
    mock_llm.generate.return_value = mock_response

    synthesizer = Synthesizer(mock_llm)

    recommendation = synthesizer.synthesize(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        technical_view="RSI is 75, indicating overbought conditions.",
        news_summary="No major news events.",
    )

    assert recommendation.symbol == "EURUSD"
    assert recommendation.timeframe == Timeframe.H1
    assert recommendation.action == "CALL"
    assert recommendation.confidence == 0.75
    assert recommendation.brief == "Strong bullish momentum with RSI above 70."
    assert isinstance(recommendation.timestamp, datetime)


def test_synthesizer_handles_json_with_code_blocks() -> None:
    mock_llm = Mock(spec=LlmProvider)
    mock_response = "```json\n" + json.dumps({
        "action": "PUT",
        "confidence": 0.6,
        "brief": "Bearish trend detected."
    }) + "\n```"
    mock_llm.generate.return_value = mock_response

    synthesizer = Synthesizer(mock_llm)

    recommendation = synthesizer.synthesize(
        symbol="GBPUSD",
        timeframe=Timeframe.H1,
        technical_view="Price below SMA 200.",
        news_summary="Negative news.",
    )

    assert recommendation.action == "PUT"
    assert recommendation.confidence == 0.6


def test_synthesizer_validates_action() -> None:
    mock_llm = Mock(spec=LlmProvider)
    mock_response = json.dumps({
        "action": "INVALID",
        "confidence": 0.5,
        "brief": "Test"
    })
    mock_llm.generate.return_value = mock_response

    synthesizer = Synthesizer(mock_llm)

    with pytest.raises(ValueError, match="Invalid action"):
        synthesizer.synthesize(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            technical_view="Test",
            news_summary="Test",
        )


def test_synthesizer_validates_confidence_range() -> None:
    mock_llm = Mock(spec=LlmProvider)
    mock_response = json.dumps({
        "action": "WAIT",
        "confidence": 1.5,
        "brief": "Test"
    })
    mock_llm.generate.return_value = mock_response

    synthesizer = Synthesizer(mock_llm)

    with pytest.raises(ValueError, match="Confidence must be between"):
        synthesizer.synthesize(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            technical_view="Test",
            news_summary="Test",
        )


def test_synthesizer_handles_missing_fields() -> None:
    mock_llm = Mock(spec=LlmProvider)
    mock_response = json.dumps({
        "action": "CALL",
        "confidence": 0.8
    })
    mock_llm.generate.return_value = mock_response

    synthesizer = Synthesizer(mock_llm)

    with pytest.raises(ValueError, match="missing 'brief' field"):
        synthesizer.synthesize(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            technical_view="Test",
            news_summary="Test",
        )


def test_synthesizer_handles_invalid_json() -> None:
    mock_llm = Mock(spec=LlmProvider)
    mock_llm.generate.return_value = "This is not JSON"

    synthesizer = Synthesizer(mock_llm)

    with pytest.raises(ValueError, match="Failed to parse LLM response"):
        synthesizer.synthesize(
            symbol="EURUSD",
            timeframe=Timeframe.H1,
            technical_view="Test",
            news_summary="Test",
        )
