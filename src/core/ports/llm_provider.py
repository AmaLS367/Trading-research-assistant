import time
from abc import ABC, abstractmethod

from src.core.models.llm import LlmRequest, LlmResponse


class HealthCheckResult:
    def __init__(self, ok: bool, reason: str = "") -> None:
        self.ok = ok
        self.reason = reason


class LlmProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        pass

    def generate_with_request(self, request: LlmRequest) -> LlmResponse:
        start_time = time.time()
        try:
            text = self.generate(
                system_prompt=request.system_prompt,
                user_prompt=request.user_prompt,
            )
            latency_ms = int((time.time() - start_time) * 1000)
            return LlmResponse(
                text=text,
                provider_name=self.get_provider_name(),
                model_name=request.model_name or "unknown",
                latency_ms=latency_ms,
                attempts=1,
                error=None,
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return LlmResponse(
                text="",
                provider_name=self.get_provider_name(),
                model_name=request.model_name or "unknown",
                latency_ms=latency_ms,
                attempts=1,
                error=str(e),
            )

    @abstractmethod
    def health_check(self) -> HealthCheckResult:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass
