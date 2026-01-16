import time
from typing import TYPE_CHECKING

from src.app.settings import LlmRoutingConfig, LlmTaskRouting, settings
from src.core.models.llm import LlmRequest, LlmResponse
from src.core.ports.llm_provider import LlmProvider
from src.core.ports.llm_provider_name import PROVIDER_OLLAMA_LOCAL
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
            logger.debug(
                f"Provider request: task={request.task}, provider={provider_name}, "
                f"model={model_name}, attempt={attempts}, "
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
            logger.debug(
                f"Provider response failed: provider={provider_name}, model={model_name}, "
                f"duration_ms={request_duration_ms:.1f}, error={response.error}, attempts={attempts}"
            )

        logger.warning(
            f"All configured providers failed for task={request.task}, "
            f"attempts={attempts}, last_error={last_error}, trying last resort"
        )
        last_resort_response = self._try_last_resort(request)
        if last_resort_response.error is None:
            last_resort_response.attempts = attempts + 1
            logger.debug(
                f"Last resort succeeded: provider={last_resort_response.provider_name}, "
                f"model={last_resort_response.model_name}, attempts={last_resort_response.attempts}"
            )
            return last_resort_response

        return LlmResponse(
            text="",
            provider_name="unknown",
            model_name="unknown",
            latency_ms=0,
            attempts=attempts + 1,
            error=last_error or "All providers failed, including last resort",
        )
