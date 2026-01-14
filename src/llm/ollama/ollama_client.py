import httpx

from src.core.ports.llm_provider import LlmProvider
from src.utils.retry import retry_network_call


class OllamaClient(LlmProvider):
    def __init__(self, base_url: str, model: str, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    @retry_network_call(max_attempts=2, min_wait=2.0, max_wait=5.0)
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
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

    def __del__(self) -> None:
        if hasattr(self, "client"):
            self.client.close()
