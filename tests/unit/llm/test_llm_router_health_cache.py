import time

from src.llm.providers.llm_router import LlmRouteStep, LlmRoutingConfig, LlmTaskRouting
from src.core.models.llm import LlmResponse
from src.core.ports.llm_provider import HealthCheckResult, LlmProvider
from src.llm.providers.llm_router import LlmRouter


class MockProviderWithHealthCheck(LlmProvider):
    def __init__(self, name: str) -> None:
        self.name = name
        self.health_check_call_count = 0

    def get_provider_name(self) -> str:
        return self.name

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return "response"

    def health_check(self) -> HealthCheckResult:
        self.health_check_call_count += 1
        return HealthCheckResult(ok=True, reason="")

    def generate_with_request(self, request) -> LlmResponse:
        return LlmResponse(
            text="response",
            provider_name=self.name,
            model_name="model",
            latency_ms=10,
            attempts=1,
            error=None,
        )


def test_health_check_cache_ttl():
    provider = MockProviderWithHealthCheck("test_provider")

    providers = {"test_provider": provider}
    routing_config = LlmRoutingConfig(
        router_mode="sequential",
        verifier_enabled=False,
        max_retries=1,
        timeout_seconds=60.0,
        temperature=0.2,
    )
    task_routing = LlmTaskRouting(steps=[LlmRouteStep(provider="test_provider", model="model1")])
    task_routings = {"test_task": task_routing}

    router = LlmRouter(providers, routing_config, task_routings)

    router._is_provider_available("test_provider")
    assert provider.health_check_call_count == 1

    router._is_provider_available("test_provider")
    assert provider.health_check_call_count == 1

    router._health_cache_ttl = 0.0
    router._is_provider_available("test_provider")
    assert provider.health_check_call_count == 2


def test_health_check_cache_expires():
    provider = MockProviderWithHealthCheck("test_provider")

    providers = {"test_provider": provider}
    routing_config = LlmRoutingConfig(
        router_mode="sequential",
        verifier_enabled=False,
        max_retries=1,
        timeout_seconds=60.0,
        temperature=0.2,
    )
    task_routing = LlmTaskRouting(steps=[LlmRouteStep(provider="test_provider", model="model1")])
    task_routings = {"test_task": task_routing}

    router = LlmRouter(providers, routing_config, task_routings)
    router._health_cache_ttl = 0.1

    router._is_provider_available("test_provider")
    assert provider.health_check_call_count == 1

    time.sleep(0.15)

    router._is_provider_available("test_provider")
    assert provider.health_check_call_count == 2
