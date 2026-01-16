from unittest.mock import Mock

from src.agents.verifier import VerifierAgent
from src.app.settings import settings
from src.core.models.llm import LlmResponse
from src.llm.providers.llm_router import LlmRouter


def test_verifier_hard_mode_does_repair(monkeypatch):
    mock_router = Mock(spec=LlmRouter)

    mock_router.generate.side_effect = [
        LlmResponse(
            text='{"passed": false, "issues": [{"code": "test", "message": "test", "severity": "medium"}], "suggested_fix": "Fix it"}',
            provider_name="test",
            model_name="test",
            latency_ms=100,
            attempts=1,
            error=None,
        ),
        LlmResponse(
            text='{"passed": true, "issues": [], "suggested_fix": null}',
            provider_name="test",
            model_name="test",
            latency_ms=100,
            attempts=1,
            error=None,
        ),
    ]

    verifier = VerifierAgent(mock_router)

    with monkeypatch.context() as m:
        m.setattr(settings, "llm_verifier_mode", "hard")
        m.setattr(settings, "llm_verifier_max_repairs", 1)

        report = verifier.verify("test_task", "Input", "Output")

        assert report.passed is False
        assert len(report.issues) == 1

        report2 = verifier.verify("test_task", "Input", "Fixed Output")

        assert report2.passed is True


def test_verifier_soft_mode_no_repair(monkeypatch):
    mock_router = Mock(spec=LlmRouter)
    mock_router.generate.return_value = LlmResponse(
        text='{"passed": false, "issues": [{"code": "test", "message": "test", "severity": "medium"}], "suggested_fix": "Fix it"}',
        provider_name="test",
        model_name="test",
        latency_ms=100,
        attempts=1,
        error=None,
    )

    verifier = VerifierAgent(mock_router)

    with monkeypatch.context() as m:
        m.setattr(settings, "llm_verifier_mode", "soft")
        m.setattr(settings, "llm_verifier_max_repairs", 1)

        report = verifier.verify("test_task", "Input", "Output")

        assert report.passed is False
        assert mock_router.generate.call_count == 1
