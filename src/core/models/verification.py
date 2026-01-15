from enum import Enum

from pydantic import BaseModel


class VerificationIssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VerificationIssue(BaseModel):
    code: str
    message: str
    severity: VerificationIssueSeverity
    evidence: str | None = None


class VerificationReport(BaseModel):
    passed: bool
    issues: list[VerificationIssue]
    suggested_fix: str | None = None
    policy_version: str = "1.0"
    provider_name: str | None = None
    model_name: str | None = None
