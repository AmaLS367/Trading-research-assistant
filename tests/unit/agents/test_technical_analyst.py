from datetime import datetime, timedelta
from unittest.mock import Mock

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

    result, llm_response = analyst.analyze(snapshot, "EURUSD", Timeframe.H1)

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

    result, llm_response = analyst.analyze(snapshot, "GBPUSD", Timeframe.H1)

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

    result, llm_response = analyst.analyze(snapshot, "GBPUSD", Timeframe.H1)

    assert result == "The GBP/USD pair shows bullish momentum with RSI above 70."
    assert "Analysis scope" not in result
    assert "ignore those references" not in result
