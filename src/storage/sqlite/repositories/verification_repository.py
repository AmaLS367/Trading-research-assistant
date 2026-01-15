import json

from src.core.models.verification import VerificationReport
from src.storage.sqlite.connection import DBConnection


class VerificationRepository:
    def __init__(self, db: DBConnection) -> None:
        self.db = db

    def create(self, run_id: int, report: VerificationReport) -> int:
        issues_json = json.dumps(
            [
                {
                    "code": issue.code,
                    "message": issue.message,
                    "severity": issue.severity.value,
                    "evidence": issue.evidence,
                }
                for issue in report.issues
            ]
        )

        query = """
            INSERT INTO verification_reports (
                run_id, passed, issues_json, suggested_fix,
                policy_version, provider_name, model_name
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(
                query,
                (
                    run_id,
                    1 if report.passed else 0,
                    issues_json,
                    report.suggested_fix,
                    report.policy_version,
                    report.provider_name,
                    report.model_name,
                ),
            )
            row_id = cursor.lastrowid
            if row_id is None:
                raise RuntimeError("Failed to get lastrowid after inserting verification report")
            return row_id

    def get_latest_by_run_id(self, run_id: int) -> VerificationReport | None:
        query = """
            SELECT id, run_id, passed, issues_json, suggested_fix,
                   policy_version, provider_name, model_name, created_at
            FROM verification_reports
            WHERE run_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (run_id,))
            row = cursor.fetchone()
            if not row:
                return None

            row_dict = dict(row)
            issues_data = json.loads(row_dict["issues_json"])

            from src.core.models.verification import (
                VerificationIssue,
                VerificationIssueSeverity,
            )

            issues = [
                VerificationIssue(
                    code=issue_data["code"],
                    message=issue_data["message"],
                    severity=VerificationIssueSeverity(issue_data["severity"]),
                    evidence=issue_data.get("evidence"),
                )
                for issue_data in issues_data
            ]

            return VerificationReport(
                passed=bool(row_dict["passed"]),
                issues=issues,
                suggested_fix=row_dict["suggested_fix"],
                policy_version=row_dict["policy_version"],
                provider_name=row_dict["provider_name"],
                model_name=row_dict["model_name"],
            )
