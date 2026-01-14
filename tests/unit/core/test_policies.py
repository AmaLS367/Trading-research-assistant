from datetime import datetime

from src.core.models.recommendation import Recommendation
from src.core.models.timeframe import Timeframe
from src.core.policies.constraints import validate_recommendation
from src.core.policies.safety_policy import SafetyPolicy, sanitize_brief


def test_validate_recommendation_valid() -> None:
    recommendation = Recommendation(
        symbol="EURUSD",
        timestamp=datetime.now(),
        timeframe=Timeframe.H1,
        action="CALL",
        brief="Test recommendation",
        confidence=0.75,
    )
    ok, error = validate_recommendation(recommendation)
    assert ok is True
    assert error is None


def test_validate_recommendation_invalid_action() -> None:
    recommendation = Recommendation(
        symbol="EURUSD",
        timestamp=datetime.now(),
        timeframe=Timeframe.H1,
        action="INVALID",
        brief="Test recommendation",
        confidence=0.75,
    )
    ok, error = validate_recommendation(recommendation)
    assert ok is False
    assert error is not None
    assert "Invalid action" in error


def test_validate_recommendation_invalid_confidence() -> None:
    recommendation = Recommendation(
        symbol="EURUSD",
        timestamp=datetime.now(),
        timeframe=Timeframe.H1,
        action="CALL",
        brief="Test recommendation",
        confidence=1.5,
    )
    ok, error = validate_recommendation(recommendation)
    assert ok is False
    assert error is not None
    assert "Confidence must be between" in error


def test_sanitize_brief_removes_imperative() -> None:
    brief = "You should execute the trade now. Make the trade."
    sanitized = sanitize_brief(brief)
    assert "execute" not in sanitized.lower() or "make" not in sanitized.lower()
    assert "manual decision" in sanitized.lower()


def test_sanitize_brief_adds_disclaimer() -> None:
    brief = "This is a normal recommendation."
    sanitized = sanitize_brief(brief)
    assert "manual decision" in sanitized.lower()


def test_safety_policy_validate_passes_valid() -> None:
    policy = SafetyPolicy()
    recommendation = Recommendation(
        symbol="EURUSD",
        timestamp=datetime.now(),
        timeframe=Timeframe.H1,
        action="CALL",
        brief="Normal recommendation text.",
        confidence=0.75,
    )
    ok, error = policy.validate(recommendation)
    assert ok is True
    assert error is None


def test_safety_policy_validate_rejects_imperative() -> None:
    policy = SafetyPolicy()
    recommendation = Recommendation(
        symbol="EURUSD",
        timestamp=datetime.now(),
        timeframe=Timeframe.H1,
        action="CALL",
        brief="You should execute the trade now.",
        confidence=0.75,
    )
    ok, error = policy.validate(recommendation)
    assert ok is False
    assert error is not None
    assert "forbidden" in error.lower()


def test_safety_policy_sanitize() -> None:
    policy = SafetyPolicy()
    recommendation = Recommendation(
        symbol="EURUSD",
        timestamp=datetime.now(),
        timeframe=Timeframe.H1,
        action="CALL",
        brief="You should execute the trade now.",
        confidence=0.75,
    )
    sanitized = policy.sanitize(recommendation)
    assert sanitized.action == "CALL"
    assert sanitized.confidence == 0.75
    assert "manual decision" in sanitized.brief.lower()
