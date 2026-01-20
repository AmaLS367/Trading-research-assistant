import pytest
from pydantic import ValidationError

from src.core.models.technical_analysis import TechnicalAnalysisResult


def test_technical_analysis_result_valid_instantiation() -> None:
    result = TechnicalAnalysisResult(
        bias="BULLISH",
        confidence=0.9,
        evidence=[],
        contradictions=[],
        setup_type=None,
        no_trade_flags=[],
    )

    assert result.bias == "BULLISH"
    assert result.confidence == 0.9
    assert result.evidence == []
    assert result.contradictions == []
    assert result.setup_type is None
    assert result.no_trade_flags == []


def test_technical_analysis_result_confidence_bounds() -> None:
    TechnicalAnalysisResult(
        bias="NEUTRAL",
        confidence=0.0,
        evidence=[],
        contradictions=[],
        setup_type=None,
        no_trade_flags=[],
    )
    TechnicalAnalysisResult(
        bias="NEUTRAL",
        confidence=1.0,
        evidence=[],
        contradictions=[],
        setup_type=None,
        no_trade_flags=[],
    )

    with pytest.raises(ValidationError):
        TechnicalAnalysisResult(
            bias="NEUTRAL",
            confidence=-0.01,
            evidence=[],
            contradictions=[],
            setup_type=None,
            no_trade_flags=[],
        )

    with pytest.raises(ValidationError):
        TechnicalAnalysisResult(
            bias="NEUTRAL",
            confidence=1.01,
            evidence=[],
            contradictions=[],
            setup_type=None,
            no_trade_flags=[],
        )


def test_technical_analysis_result_allowed_bias_values() -> None:
    for bias in ["BULLISH", "BEARISH", "NEUTRAL"]:
        result = TechnicalAnalysisResult(
            bias=bias,
            confidence=0.5,
            evidence=[],
            contradictions=[],
            setup_type=None,
            no_trade_flags=[],
        )
        assert result.bias == bias

    with pytest.raises(ValidationError):
        TechnicalAnalysisResult(
            bias="bullish",
            confidence=0.5,
            evidence=[],
            contradictions=[],
            setup_type=None,
            no_trade_flags=[],
        )
