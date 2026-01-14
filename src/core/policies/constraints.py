from src.core.models.recommendation import Recommendation

ALLOWED_ACTIONS = {"CALL", "PUT", "WAIT"}


def validate_recommendation(recommendation: Recommendation) -> tuple[bool, str | None]:
    if recommendation.action not in ALLOWED_ACTIONS:
        return False, f"Invalid action: {recommendation.action}. Must be one of {ALLOWED_ACTIONS}"

    if not 0.0 <= recommendation.confidence <= 1.0:
        return False, f"Confidence must be between 0.0 and 1.0, got {recommendation.confidence}"

    return True, None
