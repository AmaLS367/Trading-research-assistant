import time

import httpx

from src.core.models.llm import LlmRequest, LlmResponse
from src.core.ports.llm_provider import HealthCheckResult, LlmProvider


class DeepSeekClient(LlmProvider):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        provider_name: str = "deepseek_api",
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.provider_name = provider_name
        self.default_timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def get_provider_name(self) -> str:
        return self.provider_name

    def health_check(self) -> HealthCheckResult:
        if not self.api_key or not self.api_key.strip():
            return HealthCheckResult(ok=False, reason="missing api key")

        try:
            url = f"{self.base_url}/v1/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = self.client.get(url, headers=headers, timeout=5.0)
            if response.status_code == 200:
                return HealthCheckResult(ok=True, reason="")
            return HealthCheckResult(ok=False, reason=f"HTTP {response.status_code}")
        except Exception as e:
            return HealthCheckResult(ok=False, reason=str(e))

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key or not self.api_key.strip():
            raise ValueError("DeepSeek API key is required")

        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }

        response = self.client.post(url, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("Empty response from DeepSeek")

        message = choices[0].get("message", {})
        content = message.get("content", "")

        if not content:
            raise ValueError("Empty content in DeepSeek response")

        return str(content).strip()

    def generate_with_request(self, request: LlmRequest) -> LlmResponse:
        start_time = time.time()
        model_to_use = request.model_name or "deepseek-chat"
        timeout_to_use = request.timeout_seconds or self.default_timeout

        if not self.api_key or not self.api_key.strip():
            latency_ms = int((time.time() - start_time) * 1000)
            return LlmResponse(
                text="",
                provider_name=self.provider_name,
                model_name=model_to_use,
                latency_ms=latency_ms,
                attempts=1,
                error="missing api key",
            )

        try:
            url = f"{self.base_url}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": model_to_use,
                "messages": [
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_prompt},
                ],
                "temperature": request.temperature,
                "stream": False,
            }

            with httpx.Client(timeout=timeout_to_use) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    raise ValueError("Empty response from DeepSeek")

                message = choices[0].get("message", {})
                content = message.get("content", "")

                if not content:
                    raise ValueError("Empty content in DeepSeek response")

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
