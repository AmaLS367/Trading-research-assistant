from unittest.mock import Mock

from src.agents.verifier import VerifierAgent
from src.core.models.llm import LlmResponse
from src.llm.providers.llm_router import LlmRouter


def test_verifier_agent_parses_valid_json():
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
    assert len(report.issues) == 0
    assert report.provider_name == "test_provider"


def test_verifier_agent_parses_json_with_issues():
    mock_router = Mock(spec=LlmRouter)
    mock_response = LlmResponse(
        text='{"passed": false, "issues": [{"code": "unsupported_claim", "message": "Test issue", "severity": "medium"}], "suggested_fix": "Fix the issue", "policy_version": "1.0"}',
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )
    mock_router.generate.return_value = mock_response

    verifier = VerifierAgent(mock_router)
    report = verifier.verify("test_task", "Input summary", "Author output")

    assert report.passed is False
    assert len(report.issues) == 1
    assert report.issues[0].code == "unsupported_claim"
    assert report.suggested_fix == "Fix the issue"


def test_verifier_agent_handles_invalid_json():
    mock_router = Mock(spec=LlmRouter)
    mock_response = LlmResponse(
        text="This is not JSON at all",
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )
    mock_router.generate.return_value = mock_response

    verifier = VerifierAgent(mock_router)
    report = verifier.verify("test_task", "Input summary", "Author output")

    assert report.passed is False
    assert len(report.issues) == 1
    assert report.issues[0].code == "invalid_json"
    assert report.suggested_fix is not None


def test_verifier_agent_handles_json_with_code_blocks():
    mock_router = Mock(spec=LlmRouter)
    mock_response = LlmResponse(
        text='```json\n{"passed": true, "issues": []}\n```',
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
    assert len(report.issues) == 0


def test_verifier_agent_handles_non_dict_json():
    mock_router = Mock(spec=LlmRouter)
    mock_response = LlmResponse(
        text='["not", "an", "object"]',
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )
    mock_router.generate.return_value = mock_response

    verifier = VerifierAgent(mock_router)
    report = verifier.verify("test_task", "Input summary", "Author output")

    assert report.passed is False
    assert len(report.issues) == 1
    assert "not a JSON object" in report.issues[0].message
