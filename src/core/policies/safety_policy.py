import re

from src.core.models.recommendation import Recommendation
from src.core.policies.constraints import validate_recommendation

FORBIDDEN_PATTERNS = [
    r"\b(execute|place|open|close|enter|exit)\s+(trade|position|order)",
    r"\b(automatically|auto)\s+(trade|execute|place)",
    r"\b(make|do|take)\s+(the\s+)?trade",
    r"\b(you\s+should|you\s+must|you\s+need\s+to)\s+(trade|execute|place)",
]


def sanitize_brief(brief: str) -> str:
    sanitized = brief

    for pattern in FORBIDDEN_PATTERNS:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    if not sanitized.endswith("."):
        sanitized += "."

    if "manual decision" not in sanitized.lower():
        sanitized += " [Manual decision required - this is research-only analysis.]"

    return sanitized


class SafetyPolicy:
    def validate(self, recommendation: Recommendation) -> tuple[bool, str | None]:
        constraint_ok, constraint_error = validate_recommendation(recommendation)
        if not constraint_ok:
            return False, constraint_error

        brief_lower = recommendation.brief.lower()

        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, brief_lower):
                return False, f"Brief contains forbidden imperative command pattern: {pattern}"

        return True, None

    def sanitize(self, recommendation: Recommendation) -> Recommendation:
        sanitized_brief = sanitize_brief(recommendation.brief)

        return Recommendation(
            id=recommendation.id,
            run_id=recommendation.run_id,
            symbol=recommendation.symbol,
            timestamp=recommendation.timestamp,
            timeframe=recommendation.timeframe,
            action=recommendation.action,
            brief=sanitized_brief,
            confidence=recommendation.confidence,
        )
