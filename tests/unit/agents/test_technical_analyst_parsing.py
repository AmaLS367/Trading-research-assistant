from datetime import datetime
from unittest.mock import Mock

from src.agents.technical_analyst import TechnicalAnalyst
from src.core.models.candle import Candle
from src.core.models.llm import LlmResponse
from src.core.models.technical_analysis import TechnicalAnalysisResult
from src.core.models.timeframe import Timeframe
from src.features.snapshots.feature_snapshot import FeatureSnapshot
from src.llm.providers.llm_router import LlmRouter


def _create_minimal_snapshot() -> FeatureSnapshot:
    candle = Candle(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        open=1.0,
        high=1.0,
        low=1.0,
        close=1.0,
        volume=1.0,
    )

    return FeatureSnapshot(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        candles=[candle],
        indicators={},
    )


def _create_analyst_with_llm_text(text: str) -> TechnicalAnalyst:
    mock_router = Mock(spec=LlmRouter)
    mock_router.generate.return_value = LlmResponse(
        text=text,
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=1,
        attempts=1,
        error=None,
    )
    return TechnicalAnalyst(mock_router)


def test_technical_analyst_parsing_valid_json_only() -> None:
    analyst = _create_analyst_with_llm_text(
        '{"bias":"BULLISH","confidence":0.9,"evidence":["Trend: Direction=BULLISH, Strength=3.0"],'
        '"contradictions":[],"setup_type":null,"no_trade_flags":[]}'
    )
    snapshot = _create_minimal_snapshot()

    result_text, _ = analyst.analyze(snapshot, "EURUSD", Timeframe.H1)

    parsed = TechnicalAnalysisResult.model_validate_json(result_text)
    assert parsed.bias == "BULLISH"
    assert parsed.confidence == 0.9


def test_technical_analyst_parsing_json_in_fences() -> None:
    analyst = _create_analyst_with_llm_text(
        "Here you go:\n```json\n"
        '{"bias":"BEARISH","confidence":0.7,"evidence":["Crossovers: EMA9/SMA50=BEARISH (age 2)"],'
        '"contradictions":[],"setup_type":null,"no_trade_flags":[]}\n'
        "```\nThanks!"
    )
    snapshot = _create_minimal_snapshot()

    result_text, _ = analyst.analyze(snapshot, "EURUSD", Timeframe.H1)

    parsed = TechnicalAnalysisResult.model_validate_json(result_text)
    assert parsed.bias == "BEARISH"
    assert parsed.confidence == 0.7


def test_technical_analyst_parsing_invalid_json_falls_back() -> None:
    analyst = _create_analyst_with_llm_text("not json at all")
    snapshot = _create_minimal_snapshot()

    result_text, _ = analyst.analyze(snapshot, "EURUSD", Timeframe.H1)

    parsed = TechnicalAnalysisResult.model_validate_json(result_text)
    assert parsed.bias == "NEUTRAL"
    assert parsed.confidence == 0.0
    assert "PARSING_FAILED" in parsed.no_trade_flags


def test_technical_analyst_parsing_missing_required_fields_falls_back() -> None:
    analyst = _create_analyst_with_llm_text('{"confidence":0.9}')
    snapshot = _create_minimal_snapshot()

    result_text, _ = analyst.analyze(snapshot, "EURUSD", Timeframe.H1)

    parsed = TechnicalAnalysisResult.model_validate_json(result_text)
    assert parsed.bias == "NEUTRAL"
    assert parsed.confidence == 0.0
    assert "PARSING_FAILED" in parsed.no_trade_flags

