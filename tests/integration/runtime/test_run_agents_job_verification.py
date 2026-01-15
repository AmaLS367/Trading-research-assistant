import tempfile
from pathlib import Path
from unittest.mock import Mock

from src.agents.verifier import VerifierAgent
from src.app.settings import settings
from src.core.models.llm import LlmResponse
from src.core.models.verification import (
    VerificationIssue,
    VerificationIssueSeverity,
    VerificationReport,
)
from src.core.ports.llm_tasks import TASK_VERIFICATION
from src.llm.providers.llm_router import LlmRouter
from src.storage.sqlite.connection import DBConnection
from src.storage.sqlite.repositories.verification_repository import VerificationRepository


def test_verification_report_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DBConnection(str(db_path))

        db.run_migration(settings.storage_migration_path)

        repository = VerificationRepository(db)

        report = VerificationReport(
            passed=False,
            issues=[
                VerificationIssue(
                    code="unsupported_claim",
                    message="Test issue",
                    severity=VerificationIssueSeverity.MEDIUM,
                    evidence="Test evidence",
                )
            ],
            suggested_fix="Fix the issue",
            policy_version="1.0",
            provider_name="test_provider",
            model_name="test_model",
        )

        report_id = repository.create(1, report)
        assert report_id > 0

        retrieved = repository.get_latest_by_run_id(1)
        assert retrieved is not None
        assert retrieved.passed is False
        assert len(retrieved.issues) == 1
        assert retrieved.issues[0].code == "unsupported_claim"
        assert retrieved.suggested_fix == "Fix the issue"


def test_verifier_agent_integration():
    mock_router = Mock(spec=LlmRouter)
    mock_response = LlmResponse(
        text='{"passed": true, "issues": [], "suggested_fix": null, "policy_version": "1.0"}',
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )
    mock_router.generate.return_value = mock_response

    verifier = VerifierAgent(mock_router)
    report = verifier.verify("test_task", "Input summary", "Author output")

    assert report.passed is True
    mock_router.generate.assert_called_once()
    call_args = mock_router.generate.call_args
    assert call_args.kwargs["task"] == TASK_VERIFICATION
