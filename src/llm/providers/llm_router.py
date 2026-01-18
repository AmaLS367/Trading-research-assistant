from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.core.models.llm import LlmRequest, LlmResponse
from src.core.ports.llm_provider import LlmProvider
from src.utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = get_logger(__name__)


@dataclass
class LlmRouteStep:
    provider: str
    model: str


@dataclass
class LlmTaskRouting:
    steps: list[LlmRouteStep]


@dataclass
class LlmRoutingConfig:
    router_mode: str
    verifier_enabled: bool
    max_retries: int
    timeout_seconds: float
    temperature: float


@dataclass
class LastResortConfig:
    provider: str = "ollama_local"
    model: str = "llama3:latest"


@dataclass
class TaskOverrides:
    """Per-task timeout and temperature overrides."""
    timeout_seconds: float | None = None
    temperature: float | None = None


class LlmRouter:
    def __init__(
        self,
        providers: Mapping[str, LlmProvider],
        routing_config: LlmRoutingConfig,
        task_routings: Mapping[str, LlmTaskRouting],
        last_resort: LastResortConfig | None = None,
        provider_timeouts: dict[str, float] | None = None,
        task_overrides: dict[str, TaskOverrides] | None = None,
    ) -> None:
        self.providers = providers
        self.routing_config = routing_config
        self.task_routings = task_routings
        self.last_resort = last_resort or LastResortConfig()
        self.provider_timeouts = provider_timeouts or {}
        self.task_overrides = task_overrides or {}
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
                logger.debug(
                    f"Health check cached: provider={provider_name}, available={cached_ok}, cached=true"
                )
                return cached_ok

        provider = self.providers[provider_name]
        health_check_start = time.time()
        health_result = provider.health_check()
        health_check_duration_ms = (time.time() - health_check_start) * 1000
        is_available = health_result.ok

        self._health_cache[cache_key] = (is_available, current_time)
        logger.debug(
            f"Health check: provider={provider_name}, available={is_available}, "
            f"latency_ms={health_check_duration_ms:.1f}, cached=false"
        )
        return is_available

    def _get_timeout_for_provider_and_task(
        self, provider_name: str, task: str, default_timeout: float
    ) -> float:
        task_prefix_map = {
            "tech_analysis": "tech",
            "news_analysis": "news",
            "synthesis": "synthesis",
            "verification": "verifier",
        }
        task_prefix = task_prefix_map.get(task)

        provider_normalized = provider_name.replace("-", "_").replace(".", "_")

        # Check per-provider-per-task timeout
        if task_prefix:
            provider_task_timeout_key = f"{provider_normalized}_{task_prefix}_timeout_seconds"
            if provider_task_timeout_key in self.provider_timeouts:
                return self.provider_timeouts[provider_task_timeout_key]

        # Check per-provider timeout
        provider_timeout_key = f"{provider_normalized}_timeout_seconds"
        if provider_timeout_key in self.provider_timeouts:
            return self.provider_timeouts[provider_timeout_key]

        return default_timeout

    def _try_last_resort(self, request: LlmRequest) -> LlmResponse:
        provider_name = self.last_resort.provider
        model_name = self.last_resort.model

        logger.info(
            f"Trying last resort: task={request.task}, provider={provider_name}, model={model_name}"
        )

        if provider_name not in self.providers:
            return LlmResponse(
                text="",
                provider_name=provider_name,
                model_name=model_name,
                latency_ms=0,
                attempts=1,
                error=f"Last resort provider not available: {provider_name}",
            )

        provider = self.providers[provider_name]
        last_resort_request = LlmRequest(
            task=request.task,
            system_prompt=request.system_prompt,
            user_prompt=request.user_prompt,
            temperature=request.temperature,
            timeout_seconds=request.timeout_seconds,
            max_retries=request.max_retries,
            model_name=model_name,
            response_format=request.response_format,
        )

        return provider.generate_with_request(last_resort_request)

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

        # Apply per-task overrides
        if task in self.task_overrides:
            overrides = self.task_overrides[task]
            if overrides.temperature is not None:
                temperature = overrides.temperature
            if overrides.timeout_seconds is not None:
                timeout_seconds = overrides.timeout_seconds

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

        if routing_config.router_mode == "strict":
            return self._generate_strict(request, task_routing)

        return LlmResponse(
            text="",
            provider_name="unknown",
            model_name="unknown",
            latency_ms=0,
            attempts=1,
            error=f"Unsupported router mode: {routing_config.router_mode}",
        )

    def _generate_strict(self, request: LlmRequest, task_routing: LlmTaskRouting) -> LlmResponse:
        if not task_routing.steps:
            return LlmResponse(
                text="",
                provider_name="unknown",
                model_name="unknown",
                latency_ms=0,
                attempts=1,
                error=f"No routing steps configured for task={request.task}",
            )

        primary_step = task_routing.steps[0]
        provider_name = primary_step.provider
        model_name = primary_step.model

        logger.debug(
            f"Routing decision (strict mode): task={request.task}, "
            f"provider={provider_name}, model={model_name}, "
            f"temperature={request.temperature}, timeout_seconds={request.timeout_seconds}, "
            f"max_retries={request.max_retries}, fallback_disabled=true"
        )

        if not self._is_provider_available(provider_name):
            error_message = (
                f"Primary provider unavailable in strict mode: "
                f"task={request.task}, provider={provider_name}, model={model_name}"
            )
            logger.error(error_message)
            return LlmResponse(
                text="",
                provider_name=provider_name,
                model_name=model_name,
                latency_ms=0,
                attempts=1,
                error=error_message,
            )

        if provider_name not in self.providers:
            error_message = (
                f"Primary provider not found in strict mode: "
                f"task={request.task}, provider={provider_name}, model={model_name}"
            )
            logger.error(error_message)
            return LlmResponse(
                text="",
                provider_name=provider_name,
                model_name=model_name,
                latency_ms=0,
                attempts=1,
                error=error_message,
            )

        provider = self.providers[provider_name]
        provider_timeout = self._get_timeout_for_provider_and_task(
            provider_name=provider_name,
            task=request.task,
            default_timeout=request.timeout_seconds,
        )
        step_request = LlmRequest(
            task=request.task,
            system_prompt=request.system_prompt,
            user_prompt=request.user_prompt,
            temperature=request.temperature,
            timeout_seconds=provider_timeout,
            max_retries=request.max_retries,
            model_name=model_name,
            response_format=request.response_format,
        )

        logger.debug(
            f"Provider request (strict mode): task={request.task}, provider={provider_name}, "
            f"model={model_name}, timeout_seconds={provider_timeout}, "
            f"prompt_chars={len(request.system_prompt) + len(request.user_prompt)}"
        )
        request_start = time.time()
        response = provider.generate_with_request(step_request)
        request_duration_ms = (time.time() - request_start) * 1000

        if response.error is None:
            response.attempts = 1
            logger.debug(
                f"Provider response success (strict mode): provider={provider_name}, "
                f"model={model_name}, duration_ms={request_duration_ms:.1f}, "
                f"response_chars={len(response.text)}, attempts=1"
            )
            return response

        error_message = (
            f"Primary provider failed in strict mode: "
            f"task={request.task}, provider={provider_name}, model={model_name}, "
            f"error={response.error}"
        )
        logger.error(error_message)
        return LlmResponse(
            text="",
            provider_name=provider_name,
            model_name=model_name,
            latency_ms=int(request_duration_ms),
            attempts=1,
            error=error_message,
        )

    def _generate_sequential(
        self, request: LlmRequest, task_routing: LlmTaskRouting
    ) -> LlmResponse:
        attempts = 0
        last_error: str | None = None

        routing_steps = [f"{step.provider}/{step.model}" for step in task_routing.steps]
        logger.debug(
            f"Routing decision: task={request.task}, preferred_steps={routing_steps}, "
            f"temperature={request.temperature}, timeout_seconds={request.timeout_seconds}, "
            f"max_retries={request.max_retries}"
        )

        for step in task_routing.steps:
            provider_name = step.provider
            model_name = step.model

            if not self._is_provider_available(provider_name):
                logger.debug(
                    f"Provider unavailable, skipping: provider={provider_name}, model={model_name}"
                )
                continue

            if provider_name not in self.providers:
                continue

            provider = self.providers[provider_name]
            provider_timeout = self._get_timeout_for_provider_and_task(
                provider_name=provider_name,
                task=request.task,
                default_timeout=request.timeout_seconds,
            )
            step_request = LlmRequest(
                task=request.task,
                system_prompt=request.system_prompt,
                user_prompt=request.user_prompt,
                temperature=request.temperature,
                timeout_seconds=provider_timeout,
                max_retries=request.max_retries,
                model_name=model_name,
                response_format=request.response_format,
            )

            attempts += 1
            logger.debug(
                f"Provider request: task={request.task}, provider={provider_name}, "
                f"model={model_name}, attempt={attempts}, timeout_seconds={provider_timeout}, "
                f"prompt_chars={len(request.system_prompt) + len(request.user_prompt)}"
            )
            request_start = time.time()
            response = provider.generate_with_request(step_request)
            request_duration_ms = (time.time() - request_start) * 1000

            if response.error is None:
                response.attempts = attempts
                logger.debug(
                    f"Provider response success: provider={provider_name}, model={model_name}, "
                    f"duration_ms={request_duration_ms:.1f}, response_chars={len(response.text)}, "
                    f"attempts={attempts}"
                )
                return response

            last_error = response.error
            is_timeout = (
                "timeout" in str(response.error).lower()
                or "timed out" in str(response.error).lower()
            )

            if is_timeout:
                logger.error(
                    f"Provider timeout: task={request.task}, provider={provider_name}, "
                    f"model={model_name}, timeout_seconds={provider_timeout}, "
                    f"attempt={attempts}, elapsed_ms={request_duration_ms:.1f}, "
                    f"error={response.error}"
                )
            else:
                logger.debug(
                    f"Provider response failed: provider={provider_name}, model={model_name}, "
                    f"duration_ms={request_duration_ms:.1f}, error={response.error}, attempts={attempts}"
                )

            next_step_index = task_routing.steps.index(step) + 1
            if next_step_index < len(task_routing.steps):
                next_step = task_routing.steps[next_step_index]
                fallback_reason = "timeout" if is_timeout else f"error: {response.error}"
                logger.info(
                    f"Switching to fallback: reason={fallback_reason}, "
                    f"next_provider={next_step.provider}, next_model={next_step.model}"
                )

        logger.error(
            f"All configured providers failed for task={request.task}, "
            f"attempts={attempts}, last_error={last_error}, trying last resort "
            f"(provider={self.last_resort.provider}, model={self.last_resort.model})"
        )
        last_resort_response = self._try_last_resort(request)
        if last_resort_response.error is None:
            last_resort_response.attempts = attempts + 1
            logger.debug(
                f"Last resort succeeded: provider={last_resort_response.provider_name}, "
                f"model={last_resort_response.model_name}, attempts={last_resort_response.attempts}"
            )
            return last_resort_response

        error_message = (
            f"All providers failed for task={request.task}, "
            f"including last resort (provider={self.last_resort.provider}, model={self.last_resort.model}): "
            f"{last_resort_response.error}"
        )
        return LlmResponse(
            text="",
            provider_name=self.last_resort.provider,
            model_name=self.last_resort.model,
            latency_ms=0,
            attempts=attempts + 1,
            error=error_message,
        )
