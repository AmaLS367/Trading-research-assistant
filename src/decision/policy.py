from __future__ import annotations

from src.app.settings import Settings
from src.core.models.technical_analysis import TechnicalAnalysisResult
from src.decision.scoring import DecisionScores


def decide_action(
    scores: DecisionScores,
    reason_codes: list[str],
    settings: Settings,
    technical: TechnicalAnalysisResult,
) -> tuple[str, float]:
    _ = reason_codes

    action: str
    confidence: float

    if scores.no_trade_score > settings.decision_max_no_trade_score:
        action = "WAIT"
        confidence = min(0.4, float(technical.confidence))
    elif (scores.bull_score - scores.bear_score) >= settings.decision_min_trade_edge:
        action = "CALL"
        confidence = float(technical.confidence)
    elif (scores.bear_score - scores.bull_score) >= settings.decision_min_trade_edge:
        action = "PUT"
        confidence = float(technical.confidence)
    else:
        action = "WAIT"
        confidence = float(technical.confidence) * 0.7

    return action, _clamp_confidence(confidence)


def _clamp_confidence(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)
