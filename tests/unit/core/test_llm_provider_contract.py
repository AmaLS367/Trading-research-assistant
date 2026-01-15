from src.core.models.llm import LlmRequest, LlmResponse
from src.core.ports.llm_provider import HealthCheckResult, LlmProvider


class TestLlmProvider(LlmProvider):
    def __init__(self) -> None:
        self.generate_called = False
        self.health_check_called = False

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.generate_called = True
        return "test response"

    def health_check(self) -> HealthCheckResult:
        self.health_check_called = True
        return HealthCheckResult(ok=True, reason="test")

    def get_provider_name(self) -> str:
        return "test_provider"


def test_llm_provider_implements_required_methods():
    provider = TestLlmProvider()
    assert hasattr(provider, "generate")
    assert hasattr(provider, "generate_with_request")
    assert hasattr(provider, "health_check")
    assert hasattr(provider, "get_provider_name")


def test_generate_with_request_calls_generate():
    provider = TestLlmProvider()
    request = LlmRequest(
        task="test",
        system_prompt="system",
        user_prompt="user",
        temperature=0.2,
        timeout_seconds=60.0,
        max_retries=1,
        model_name="test-model",
    )

    response = provider.generate_with_request(request)

    assert provider.generate_called is True
    assert isinstance(response, LlmResponse)
    assert response.text == "test response"
    assert response.provider_name == "test_provider"
    assert response.model_name == "test-model"
    assert response.latency_ms >= 0
    assert response.attempts == 1
    assert response.error is None


def test_generate_with_request_handles_exception():
    class FailingProvider(LlmProvider):
        def generate(self, system_prompt: str, user_prompt: str) -> str:
            raise ValueError("test error")

        def health_check(self) -> HealthCheckResult:
            return HealthCheckResult(ok=False, reason="error")

        def get_provider_name(self) -> str:
            return "failing_provider"

    provider = FailingProvider()
    request = LlmRequest(
        task="test",
        system_prompt="system",
        user_prompt="user",
        temperature=0.2,
        timeout_seconds=60.0,
        max_retries=1,
    )

    response = provider.generate_with_request(request)

    assert response.text == ""
    assert response.error == "test error"
    assert response.provider_name == "failing_provider"


def test_health_check_returns_result():
    provider = TestLlmProvider()
    result = provider.health_check()

    assert provider.health_check_called is True
    assert isinstance(result, HealthCheckResult)
    assert result.ok is True
    assert result.reason == "test"
