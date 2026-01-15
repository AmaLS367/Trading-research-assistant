from datetime import datetime, timedelta
from unittest.mock import Mock

import httpx
import pytest

from src.agents.technical_analyst import TechnicalAnalyst
from src.core.models.candle import Candle
from src.core.models.llm import LlmResponse
from src.features.indicators.indicator_engine import calculate_features
from src.features.snapshots.feature_snapshot import FeatureSnapshot
from src.llm.providers.llm_router import LlmRouter


def create_test_candles(count: int, base_price: float = 1.1000) -> list[Candle]:
    candles: list[Candle] = []
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    for i in range(count):
        price_variation = (i % 10) * 0.0001
        candles.append(
            Candle(
                timestamp=base_time + timedelta(hours=i),
                open=base_price + price_variation,
                high=base_price + price_variation + 0.0010,
                low=base_price + price_variation - 0.0010,
                close=base_price + price_variation + 0.0005,
                volume=1000.0 + i * 10,
            )
        )

    return candles


def test_technical_analyst_analyze() -> None:
    from src.core.models.timeframe import Timeframe

    mock_router = Mock(spec=LlmRouter)
    mock_router.generate.return_value = LlmResponse(
        text="Market shows bullish momentum with RSI above 70.",
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )

    analyst = TechnicalAnalyst(mock_router)

    candles = create_test_candles(250)
    indicators = calculate_features(candles)
    snapshot = FeatureSnapshot(
        timestamp=datetime.now(),
        candles=candles,
        indicators=indicators,
    )

    result = analyst.analyze(snapshot, "EURUSD", Timeframe.H1)

    assert "Market shows bullish momentum with RSI above 70." in result
    mock_router.generate.assert_called_once()
    call_args = mock_router.generate.call_args
    assert "task" in call_args.kwargs
    assert "system_prompt" in call_args.kwargs
    assert "user_prompt" in call_args.kwargs
    assert "EUR/USD" in call_args.kwargs["system_prompt"]
    assert "1h" in call_args.kwargs["system_prompt"]


def test_technical_analyst_output_guard_wrong_pair() -> None:
    from src.core.models.timeframe import Timeframe

    mock_router = Mock(spec=LlmRouter)
    mock_router.generate.return_value = LlmResponse(
        text="The EUR/USD pair shows bullish momentum with RSI above 70.",
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )

    analyst = TechnicalAnalyst(mock_router)

    candles = create_test_candles(250)
    indicators = calculate_features(candles)
    snapshot = FeatureSnapshot(
        timestamp=datetime.now(),
        candles=candles,
        indicators=indicators,
    )

    result = analyst.analyze(snapshot, "GBPUSD", Timeframe.H1)

    assert "Analysis scope: GBP/USD" in result
    assert "model mentioned other instruments" in result
    assert "ignore those references" in result
    assert "GBP/USD" in result
    assert "EUR/USD" not in result


def test_technical_analyst_output_guard_correct_pair() -> None:
    from src.core.models.timeframe import Timeframe

    mock_router = Mock(spec=LlmRouter)
    mock_router.generate.return_value = LlmResponse(
        text="The GBP/USD pair shows bullish momentum with RSI above 70.",
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )

    analyst = TechnicalAnalyst(mock_router)

    candles = create_test_candles(250)
    indicators = calculate_features(candles)
    snapshot = FeatureSnapshot(
        timestamp=datetime.now(),
        candles=candles,
        indicators=indicators,
    )

    result = analyst.analyze(snapshot, "GBPUSD", Timeframe.H1)

    assert result == "The GBP/USD pair shows bullish momentum with RSI above 70."
    assert "Analysis scope" not in result
    assert "ignore those references" not in result


def test_ollama_client_generate() -> None:
    mock_response_data = {
        "message": {
            "role": "assistant",
            "content": "Technical analysis shows strong bullish trend.",
        }
    }

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200

    mock_client = Mock(spec=httpx.Client)
    mock_client.post.return_value = mock_response

    client = OllamaClient(base_url="http://localhost:11434", model="test-model")
    client.client = mock_client

    result = client.generate(
        system_prompt="You are a Forex expert.",
        user_prompt="RSI is 75.",
    )

    assert result == "Technical analysis shows strong bullish trend."
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert call_args.kwargs["json"]["model"] == "test-model"
    assert len(call_args.kwargs["json"]["messages"]) == 2


def test_ollama_client_handles_empty_response() -> None:
    mock_response_data = {"message": {"role": "assistant", "content": ""}}

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200

    mock_client = Mock(spec=httpx.Client)
    mock_client.post.return_value = mock_response

    client = OllamaClient(base_url="http://localhost:11434", model="test-model")
    client.client = mock_client

    with pytest.raises(ValueError, match="Empty response from Ollama"):
        client.generate(
            system_prompt="You are a Forex expert.",
            user_prompt="RSI is 75.",
        )
