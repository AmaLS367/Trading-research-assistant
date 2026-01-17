import time
from typing import TYPE_CHECKING

from src.app.settings import LlmRoutingConfig, LlmTaskRouting, settings
from src.core.models.llm import LlmRequest, LlmResponse
from src.core.ports.llm_provider import LlmProvider
from src.utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = get_logger(__name__)


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

        if task_prefix:
            provider_task_timeout_attr = f"{provider_normalized}_{task_prefix}_timeout_seconds"
            provider_task_timeout = getattr(settings, provider_task_timeout_attr, None)
            if provider_task_timeout is not None and isinstance(
                provider_task_timeout, (int, float)
            ):
                return float(provider_task_timeout)

        provider_timeout_attr = f"{provider_normalized}_timeout_seconds"
        provider_timeout = getattr(settings, provider_timeout_attr, None)
        if provider_timeout is not None and isinstance(provider_timeout, (int, float)):
            return float(provider_timeout)

        return default_timeout

    def _try_last_resort(self, request: LlmRequest) -> LlmResponse:
        last_resort = settings.llm_last_resort
        provider_name = last_resort.provider
        model_name = last_resort.model

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

        last_resort = settings.llm_last_resort
        logger.error(
            f"All configured providers failed for task={request.task}, "
            f"attempts={attempts}, last_error={last_error}, trying last resort "
            f"(provider={last_resort.provider}, model={last_resort.model})"
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
            f"including last resort (provider={last_resort.provider}, model={last_resort.model}): "
            f"{last_resort_response.error}"
        )
        return LlmResponse(
            text="",
            provider_name=last_resort.provider,
            model_name=last_resort.model,
            latency_ms=0,
            attempts=attempts + 1,
            error=error_message,
        )
