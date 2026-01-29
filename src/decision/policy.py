from __future__ import annotations

from src.app.settings import Settings
from src.core.models.technical_analysis import TechnicalAnalysisResult
from src.decision.reason_codes import CONFLICT_TREND_STRUCTURE
from src.decision.scoring import DecisionScores


def decide_action(
    scores: DecisionScores,
    reason_codes: list[str],
    settings: Settings,
    technical: TechnicalAnalysisResult,
    news_quality: str | None = None,
) -> tuple[str, float]:
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

    calibrated = _calibrate_confidence(
        action=action,
        confidence=confidence,
        reason_codes=reason_codes,
        settings=settings,
        news_quality=news_quality,
    )
    return action, calibrated


def _calibrate_confidence(
    action: str,
    confidence: float,
    reason_codes: list[str],
    settings: Settings,
    news_quality: str | None,
) -> float:
    calibrated = float(confidence)

    if isinstance(news_quality, str) and news_quality.strip().upper() == "LOW":
        calibrated = min(calibrated, float(settings.decision_max_confidence_when_news_low))

    if CONFLICT_TREND_STRUCTURE in reason_codes:
        calibrated = calibrated * 0.8

    if action == "WAIT":
        calibrated = min(calibrated, 0.5)

    return _clamp_confidence(calibrated)


def _clamp_confidence(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)
