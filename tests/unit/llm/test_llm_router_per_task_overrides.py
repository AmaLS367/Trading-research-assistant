from unittest.mock import Mock

from src.core.models.llm import LlmRequest, LlmResponse
from src.core.ports.llm_provider import LlmProvider
from src.core.ports.llm_tasks import TASK_SYNTHESIS, TASK_TECH_ANALYSIS
from src.llm.providers.llm_router import (
    LlmRouter,
    LlmRoutingConfig,
    LlmTaskRouting,
    TaskOverrides,
)


def test_per_task_temperature_override():
    """Task overrides should be applied when specified."""
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

    # Specify task overrides for tech_analysis
    task_overrides = {
        TASK_TECH_ANALYSIS: TaskOverrides(temperature=0.5, timeout_seconds=120.0)
    }

    router = LlmRouter(
        providers=providers,
        routing_config=routing_config,
        task_routings=task_routings,
        task_overrides=task_overrides,
    )

    router.generate(
        task=TASK_TECH_ANALYSIS,
        system_prompt="test",
        user_prompt="test",
    )

    call_args = mock_provider.generate_with_request.call_args
    request: LlmRequest = call_args[0][0]
    assert request.temperature == 0.5
    assert request.timeout_seconds == 120.0


def test_per_task_overrides_fallback_to_defaults():
    """Without task overrides, routing config defaults should be used."""
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

    # No task overrides
    router = LlmRouter(
        providers=providers,
        routing_config=routing_config,
        task_routings=task_routings,
    )

    router.generate(
        task=TASK_SYNTHESIS,
        system_prompt="test",
        user_prompt="test",
    )

    call_args = mock_provider.generate_with_request.call_args
    request: LlmRequest = call_args[0][0]
    assert request.temperature == 0.2
    assert request.timeout_seconds == 60.0
