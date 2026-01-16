import time
from typing import TYPE_CHECKING

from src.app.settings import LlmRoutingConfig, LlmTaskRouting, settings
from src.core.models.llm import LlmRequest, LlmResponse
from src.core.ports.llm_provider import LlmProvider
from src.core.ports.llm_provider_name import PROVIDER_OLLAMA_LOCAL

if TYPE_CHECKING:
    from collections.abc import Mapping


class LlmRouter:
    def __init__(
        self,
        providers: "Mapping[str, LlmProvider]",
        routing_config: LlmRoutingConfig,
        task_routings: "Mapping[str, LlmTaskRouting]",
    ) -> None:
        self.providers = providers
        self.routing_config = routing_config
        self.task_routings = task_routings
        self._health_cache: dict[str, tuple[bool, float]] = {}
        self._health_cache_ttl = 30.0

    def _is_provider_available(self, provider_name: str) -> bool:
        if provider_name not in self.providers:
            return False

        cache_key = provider_name
        current_time = time.time()

        if cache_key in self._health_cache:
            cached_ok, cached_time = self._health_cache[cache_key]
            if current_time - cached_time < self._health_cache_ttl:
                return cached_ok

        provider = self.providers[provider_name]
        health_result = provider.health_check()
        is_available = health_result.ok

        self._health_cache[cache_key] = (is_available, current_time)
        return is_available

    def _try_last_resort(self, request: LlmRequest) -> LlmResponse:
        if PROVIDER_OLLAMA_LOCAL not in self.providers:
            return LlmResponse(
                text="",
                provider_name="unknown",
                model_name="unknown",
                latency_ms=0,
                attempts=1,
                error="No local Ollama provider available as last resort",
            )

        local_provider = self.providers[PROVIDER_OLLAMA_LOCAL]
        last_resort_request = LlmRequest(
            task=request.task,
            system_prompt=request.system_prompt,
            user_prompt=request.user_prompt,
            temperature=request.temperature,
            timeout_seconds=request.timeout_seconds,
            max_retries=request.max_retries,
            model_name="llama3:latest",
            response_format=request.response_format,
        )

        return local_provider.generate_with_request(last_resort_request)

    def generate(self, task: str, system_prompt: str, user_prompt: str) -> LlmResponse:
        if task not in self.task_routings:
            return LlmResponse(
                text="",
                provider_name="unknown",
                model_name="unknown",
                latency_ms=0,
                attempts=1,
                error=f"Unknown task: {task}",
            )

        task_routing = self.task_routings[task]
        routing_config = self.routing_config

        temperature = routing_config.temperature
        timeout_seconds = routing_config.timeout_seconds

        task_prefix_map = {
            "tech_analysis": "tech",
            "news_analysis": "news",
            "synthesis": "synthesis",
            "verification": "verifier",
        }
        task_prefix = task_prefix_map.get(task)
        if task_prefix:
            task_temperature = getattr(settings, f"{task_prefix}_temperature", None)
            task_timeout = getattr(settings, f"{task_prefix}_timeout_seconds", None)
            if task_temperature is not None:
                temperature = task_temperature
            if task_timeout is not None:
                timeout_seconds = task_timeout

        request = LlmRequest(
            task=task,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
            max_retries=routing_config.max_retries,
            model_name=None,
            response_format=None,
        )

        if routing_config.router_mode == "sequential":
            return self._generate_sequential(request, task_routing)

        return LlmResponse(
            text="",
            provider_name="unknown",
            model_name="unknown",
            latency_ms=0,
            attempts=1,
            error=f"Unsupported router mode: {routing_config.router_mode}",
        )

    def _generate_sequential(
        self, request: LlmRequest, task_routing: LlmTaskRouting
    ) -> LlmResponse:
        attempts = 0
        last_error: str | None = None

        for step in task_routing.steps:
            provider_name = step.provider
            model_name = step.model

            if not self._is_provider_available(provider_name):
                continue

            if provider_name not in self.providers:
                continue

            provider = self.providers[provider_name]
            step_request = LlmRequest(
                task=request.task,
                system_prompt=request.system_prompt,
                user_prompt=request.user_prompt,
                temperature=request.temperature,
                timeout_seconds=request.timeout_seconds,
                max_retries=request.max_retries,
                model_name=model_name,
                response_format=request.response_format,
            )

            attempts += 1
            response = provider.generate_with_request(step_request)

            if response.error is None:
                response.attempts = attempts
                return response

            last_error = response.error

        last_resort_response = self._try_last_resort(request)
        if last_resort_response.error is None:
            last_resort_response.attempts = attempts + 1
            return last_resort_response

        return LlmResponse(
            text="",
            provider_name="unknown",
            model_name="unknown",
            latency_ms=0,
            attempts=attempts + 1,
            error=last_error or "All providers failed, including last resort",
        )
