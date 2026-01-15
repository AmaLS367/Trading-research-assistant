import time

import httpx

from src.core.models.llm import LlmRequest, LlmResponse
from src.core.ports.llm_provider import HealthCheckResult, LlmProvider
from src.utils.retry import retry_network_call


class OllamaClient(LlmProvider):
    def __init__(
        self, base_url: str, model: str = "", provider_name: str = "ollama", timeout: float = 120.0
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.provider_name = provider_name
        self.default_timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def get_provider_name(self) -> str:
        return self.provider_name

    def health_check(self) -> HealthCheckResult:
        try:
            url = f"{self.base_url}/api/tags"
            response = self.client.get(url, timeout=5.0)
            if response.status_code == 200:
                return HealthCheckResult(ok=True, reason="")
            return HealthCheckResult(ok=False, reason=f"HTTP {response.status_code}")
        except Exception as e:
            return HealthCheckResult(ok=False, reason=str(e))

    @retry_network_call(max_attempts=2, min_wait=2.0, max_wait=5.0)
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        model_to_use = self.model or "llama3:latest"
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": model_to_use,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }

        response = self.client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        message = data.get("message", {})
        content = message.get("content", "")

        if not content:
            raise ValueError("Empty response from Ollama")

        result: str = str(content).strip()
        return result

    def generate_with_request(self, request: LlmRequest) -> LlmResponse:
        start_time = time.time()
        model_to_use = request.model_name or self.model or "llama3:latest"
        timeout_to_use = request.timeout_seconds or self.default_timeout

        try:
            url = f"{self.base_url}/api/chat"

            payload = {
                "model": model_to_use,
                "messages": [
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_prompt},
                ],
                "stream": False,
            }

            with httpx.Client(timeout=timeout_to_use) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()
                message = data.get("message", {})
                content = message.get("content", "")

                if not content:
                    raise ValueError("Empty response from Ollama")

                text = str(content).strip()
                latency_ms = int((time.time() - start_time) * 1000)

                return LlmResponse(
                    text=text,
                    provider_name=self.provider_name,
                    model_name=model_to_use,
                    latency_ms=latency_ms,
                    attempts=1,
                    error=None,
                )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return LlmResponse(
                text="",
                provider_name=self.provider_name,
                model_name=model_to_use,
                latency_ms=latency_ms,
                attempts=1,
                error=str(e),
            )

    def __del__(self) -> None:
        if hasattr(self, "client"):
            self.client.close()
