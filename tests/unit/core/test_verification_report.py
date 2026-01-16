from src.core.models.verification import (
    VerificationIssue,
    VerificationIssueSeverity,
    VerificationReport,
)
from src.core.policies.safety_policy import SafetyPolicy


def test_verification_report_creation():
    report = VerificationReport(
        passed=True,
        issues=[],
        suggested_fix=None,
        policy_version="1.0",
    )

    assert report.passed is True
    assert len(report.issues) == 0
    assert report.suggested_fix is None


def test_verification_report_with_issues():
    issue = VerificationIssue(
        code="unsupported_claim",
        message="Claim about price not supported by input data",
        severity=VerificationIssueSeverity.MEDIUM,
        evidence="Output mentions price 1.2500 but input shows 1.2400",
    )

    report = VerificationReport(
        passed=False,
        issues=[issue],
        suggested_fix="Remove unsupported price claim or correct to match input data",
        policy_version="1.0",
    )

    assert report.passed is False
    assert len(report.issues) == 1
    assert report.issues[0].code == "unsupported_claim"
    assert report.suggested_fix is not None


def test_safety_policy_validate_report_passed_with_issues():
    policy = SafetyPolicy()

    report = VerificationReport(
        passed=True,
        issues=[
            VerificationIssue(
                code="test",
                message="test",
                severity=VerificationIssueSeverity.LOW,
            )
        ],
    )

    valid, error = policy.validate_report(report)
    assert valid is False
    assert error is not None
    assert "passed but contains issues" in error


def test_safety_policy_validate_report_failed_without_issues():
    policy = SafetyPolicy()

    report = VerificationReport(
        passed=False,
        issues=[],
        suggested_fix="Fix something",
    )

    valid, error = policy.validate_report(report)
    assert valid is False
    assert error is not None
    assert "failed but has no issues" in error


def test_safety_policy_validate_report_failed_without_fix():
    policy = SafetyPolicy()

    report = VerificationReport(
        passed=False,
        issues=[
            VerificationIssue(
                code="test",
                message="test",
                severity=VerificationIssueSeverity.MEDIUM,
            )
        ],
        suggested_fix=None,
    )

    valid, error = policy.validate_report(report)
    assert valid is False
    assert error is not None
    assert "failed but has no suggested_fix" in error


def test_safety_policy_validate_report_valid():
    policy = SafetyPolicy()

    report = VerificationReport(
        passed=True,
        issues=[],
        suggested_fix=None,
    )

    valid, error = policy.validate_report(report)
    assert valid is True
    assert error is None


def test_safety_policy_get_verifier_rules():
    policy = SafetyPolicy()
    rules = policy.get_verifier_rules()

    assert isinstance(rules, str)
    assert "verification agent" in rules.lower()
    assert "FORBIDDEN PATTERNS" in rules
    assert "HALLUCINATION CHECK" in rules
    assert "policy_version" in rules
