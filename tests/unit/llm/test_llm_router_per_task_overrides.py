from unittest.mock import Mock

from src.app.settings import LlmRoutingConfig, LlmTaskRouting
from src.core.models.llm import LlmRequest, LlmResponse
from src.core.ports.llm_provider import LlmProvider
from src.core.ports.llm_tasks import TASK_SYNTHESIS, TASK_TECH_ANALYSIS
from src.llm.providers.llm_router import LlmRouter


def test_per_task_temperature_override(monkeypatch):
    from src.app.settings import settings

    mock_provider = Mock(spec=LlmProvider)
    mock_provider.get_provider_name.return_value = "test_provider"
    mock_provider.health_check.return_value = Mock(ok=True, reason="test")
    mock_provider.generate_with_request.return_value = LlmResponse(
        text="test",
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )

    providers: dict[str, LlmProvider] = {"test_provider": mock_provider}
    routing_config = LlmRoutingConfig(
        router_mode="sequential",
        verifier_enabled=False,
        max_retries=1,
        timeout_seconds=60.0,
        temperature=0.2,
    )

    task_routings: dict[str, LlmTaskRouting] = {
        TASK_TECH_ANALYSIS: LlmTaskRouting(
            steps=[Mock(provider="test_provider", model="test_model")]
        )
    }

    router = LlmRouter(providers, routing_config, task_routings)

    with monkeypatch.context() as m:
        m.setattr(settings, "tech_temperature", 0.5)
        m.setattr(settings, "tech_timeout_seconds", 120.0)

        router.generate(
            task=TASK_TECH_ANALYSIS,
            system_prompt="test",
            user_prompt="test",
        )

        call_args = mock_provider.generate_with_request.call_args
        request: LlmRequest = call_args[0][0]
        assert request.temperature == 0.5
        assert request.timeout_seconds == 120.0


def test_per_task_overrides_fallback_to_defaults(monkeypatch):
    from src.app.settings import settings

    mock_provider = Mock(spec=LlmProvider)
    mock_provider.get_provider_name.return_value = "test_provider"
    mock_provider.health_check.return_value = Mock(ok=True, reason="test")
    mock_provider.generate_with_request.return_value = LlmResponse(
        text="test",
        provider_name="test_provider",
        model_name="test_model",
        latency_ms=100,
        attempts=1,
        error=None,
    )

    providers: dict[str, LlmProvider] = {"test_provider": mock_provider}
    routing_config = LlmRoutingConfig(
        router_mode="sequential",
        verifier_enabled=False,
        max_retries=1,
        timeout_seconds=60.0,
        temperature=0.2,
    )

    task_routings: dict[str, LlmTaskRouting] = {
        TASK_SYNTHESIS: LlmTaskRouting(steps=[Mock(provider="test_provider", model="test_model")])
    }

    router = LlmRouter(providers, routing_config, task_routings)

    with monkeypatch.context() as m:
        m.setattr(settings, "synthesis_temperature", None)
        m.setattr(settings, "synthesis_timeout_seconds", None)

        router.generate(
            task=TASK_SYNTHESIS,
            system_prompt="test",
            user_prompt="test",
        )

        call_args = mock_provider.generate_with_request.call_args
        request: LlmRequest = call_args[0][0]
        assert request.temperature == 0.2
        assert request.timeout_seconds == 60.0
