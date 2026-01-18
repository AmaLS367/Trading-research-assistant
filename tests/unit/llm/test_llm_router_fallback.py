from src.core.models.llm import LlmRequest, LlmResponse
from src.core.ports.llm_provider import HealthCheckResult, LlmProvider
from src.core.ports.llm_provider_name import PROVIDER_OLLAMA_SERVER
from src.llm.providers.llm_router import (
    LlmRouteStep,
    LlmRouter,
    LlmRoutingConfig,
    LlmTaskRouting,
)


class MockProvider(LlmProvider):
    def __init__(self, name: str, available: bool = True, should_fail: bool = False) -> None:
        self.name = name
        self.available = available
        self.should_fail = should_fail
        self.generate_called = False

    def get_provider_name(self) -> str:
        return self.name

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.generate_called = True
        if self.should_fail:
            raise ValueError("Provider failed")
        return f"response from {self.name}"

    def health_check(self) -> HealthCheckResult:
        return HealthCheckResult(ok=self.available, reason="" if self.available else "unavailable")

    def generate_with_request(self, request: LlmRequest) -> LlmResponse:
        self.generate_called = True
        if self.should_fail:
            return LlmResponse(
                text="",
                provider_name=self.name,
                model_name=request.model_name or "unknown",
                latency_ms=10,
                attempts=1,
                error="Provider failed",
            )
        return LlmResponse(
            text=f"response from {self.name}",
            provider_name=self.name,
            model_name=request.model_name or "unknown",
            latency_ms=10,
            attempts=1,
            error=None,
        )


def test_router_fallback_primary_unavailable():
    primary = MockProvider("primary", available=False)
    fallback = MockProvider("fallback", available=True)

    providers = {"primary": primary, "fallback": fallback}
    routing_config = LlmRoutingConfig(
        router_mode="sequential",
        verifier_enabled=False,
        max_retries=1,
        timeout_seconds=60.0,
        temperature=0.2,
    )
    task_routing = LlmTaskRouting(
        steps=[
            LlmRouteStep(provider="primary", model="model1"),
            LlmRouteStep(provider="fallback", model="model2"),
        ]
    )
    task_routings = {"test_task": task_routing}

    router = LlmRouter(providers, routing_config, task_routings)
    response = router.generate("test_task", "system", "user")

    assert response.text == "response from fallback"
    assert response.provider_name == "fallback"
    assert not primary.generate_called
    assert fallback.generate_called


def test_router_fallback_primary_fails():
    primary = MockProvider("primary", available=True, should_fail=True)
    fallback = MockProvider("fallback", available=True)

    providers = {"primary": primary, "fallback": fallback}
    routing_config = LlmRoutingConfig(
        router_mode="sequential",
        verifier_enabled=False,
        max_retries=1,
        timeout_seconds=60.0,
        temperature=0.2,
    )
    task_routing = LlmTaskRouting(
        steps=[
            LlmRouteStep(provider="primary", model="model1"),
            LlmRouteStep(provider="fallback", model="model2"),
        ]
    )
    task_routings = {"test_task": task_routing}

    router = LlmRouter(providers, routing_config, task_routings)
    response = router.generate("test_task", "system", "user")

    assert response.text == "response from fallback"
    assert response.provider_name == "fallback"
    assert primary.generate_called
    assert fallback.generate_called
    assert response.attempts == 2


def test_router_last_resort():
    primary = MockProvider("primary", available=True, should_fail=True)
    fallback = MockProvider("fallback", available=True, should_fail=True)
    last_resort = MockProvider("ollama_local", available=True)

    providers = {"primary": primary, "fallback": fallback, "ollama_local": last_resort}
    routing_config = LlmRoutingConfig(
        router_mode="sequential",
        verifier_enabled=False,
        max_retries=1,
        timeout_seconds=60.0,
        temperature=0.2,
    )
    task_routing = LlmTaskRouting(
        steps=[
            LlmRouteStep(provider="primary", model="model1"),
            LlmRouteStep(provider="fallback", model="model2"),
        ]
    )
    task_routings = {"test_task": task_routing}

    router = LlmRouter(providers, routing_config, task_routings)
    response = router.generate("test_task", "system", "user")

    assert response.text == "response from ollama_local"
    assert response.provider_name == "ollama_local"
    assert response.model_name == "llama3:latest"
    assert response.attempts == 3


def test_router_unknown_task():
    providers: dict[str, LlmProvider] = {}
    routing_config = LlmRoutingConfig(
        router_mode="sequential",
        verifier_enabled=False,
        max_retries=1,
        timeout_seconds=60.0,
        temperature=0.2,
    )
    task_routings: dict[str, LlmTaskRouting] = {}

    router = LlmRouter(providers, routing_config, task_routings)
    response = router.generate("unknown_task", "system", "user")

    assert response.error is not None
    assert "Unknown task" in response.error


def test_router_skips_disabled_ollama_server():
    primary = MockProvider("primary", available=True, should_fail=True)
    disabled_server = MockProvider(PROVIDER_OLLAMA_SERVER, available=True)

    providers = {"primary": primary}
    routing_config = LlmRoutingConfig(
        router_mode="sequential",
        verifier_enabled=False,
        max_retries=1,
        timeout_seconds=60.0,
        temperature=0.2,
    )
    task_routing = LlmTaskRouting(
        steps=[
            LlmRouteStep(provider="primary", model="model1"),
            LlmRouteStep(provider=PROVIDER_OLLAMA_SERVER, model="model2"),
        ]
    )
    task_routings = {"test_task": task_routing}

    router = LlmRouter(providers, routing_config, task_routings)
    response = router.generate("test_task", "system", "user")

    assert not disabled_server.generate_called
    assert response.error is not None


def test_router_all_failed_logs_error(caplog):
    primary = MockProvider("primary", available=True, should_fail=True)
    fallback = MockProvider("fallback", available=True, should_fail=True)

    providers = {"primary": primary, "fallback": fallback}
    routing_config = LlmRoutingConfig(
        router_mode="sequential",
        verifier_enabled=False,
        max_retries=1,
        timeout_seconds=60.0,
        temperature=0.2,
    )
    task_routing = LlmTaskRouting(
        steps=[
            LlmRouteStep(provider="primary", model="model1"),
            LlmRouteStep(provider="fallback", model="model2"),
        ]
    )
    task_routings = {"test_task": task_routing}

    router = LlmRouter(providers, routing_config, task_routings)

    with caplog.at_level("ERROR"):
        response = router.generate("test_task", "system", "user")

    error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
    assert len(error_logs) > 0
    assert any("All configured providers failed" in str(record.message) for record in error_logs)
    assert response.error is not None
