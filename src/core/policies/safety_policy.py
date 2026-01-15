import re

from src.core.models.recommendation import Recommendation
from src.core.models.verification import VerificationReport
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

    def get_verifier_rules(self) -> str:
        rules = """You are a verification agent for a trading research assistant. Your role is to verify that agent outputs comply with safety policies and do not contain hallucinations or unsupported claims.

VERIFICATION RULES:

1. ACTION VALIDATION:
   - Action must be one of: CALL, PUT, WAIT
   - Confidence must be between 0.0 and 1.0
   - Brief must not contain imperative trading commands

2. FORBIDDEN PATTERNS:
   The following patterns are FORBIDDEN in briefs:
   - "execute trade", "place order", "open position"
   - "automatically trade", "auto execute"
   - "make the trade", "do the trade"
   - "you should trade", "you must execute"

3. HALLUCINATION CHECK:
   - Verify that all claims in the output are supported by the input data
   - Check for unsupported numerical claims (prices, percentages, dates)
   - Ensure no facts are invented that were not in the input

4. CONSISTENCY CHECK:
   - Verify that the action (CALL/PUT/WAIT) is consistent with the brief explanation
   - Check that confidence level matches the strength of reasoning

5. POLICY COMPLIANCE:
   - All outputs must emphasize "research-only" and "manual decision required"
   - No automated trading suggestions
   - No guarantees of profitability

ISSUE CODES:
- "unsupported_claim": Output contains claims not supported by input data
- "policy_violation": Output violates safety policy (forbidden patterns)
- "inconsistent": Action and brief are inconsistent
- "invalid_json": Response is not valid JSON

SEVERITY LEVELS:
- "low": Minor inconsistencies or style issues
- "medium": Policy violations or unsupported claims
- "high": Critical safety violations or major hallucinations

Return a VerificationReport in JSON format with:
- passed: boolean
- issues: list of VerificationIssue objects
- suggested_fix: string (if passed=false)
- policy_version: "1.0"
"""
        return rules

    def validate_report(self, report: VerificationReport) -> tuple[bool, str | None]:
        if report.passed and len(report.issues) > 0:
            return False, "Report marked as passed but contains issues"

        if not report.passed and not report.issues:
            return False, "Report marked as failed but has no issues"

        if not report.passed and not report.suggested_fix:
            return False, "Report marked as failed but has no suggested_fix"

        for issue in report.issues:
            if not issue.code:
                return False, "Issue missing code"
            if not issue.message:
                return False, "Issue missing message"
            if issue.severity.value not in ["low", "medium", "high"]:
                return False, f"Invalid severity: {issue.severity.value}"

        return True, None
