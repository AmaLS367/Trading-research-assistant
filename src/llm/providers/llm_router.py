from src.app.settings import settings
from src.core.ports.llm_provider import LlmProvider
from src.llm.ollama.ollama_client import OllamaClient


class LlmRouter:
    def __init__(self) -> None:
        self._local_provider: LlmProvider | None = None
        self._remote_provider: LlmProvider | None = None

    def get_provider(self, task: str) -> LlmProvider:
        if not settings.ollama_model:
            raise ValueError("OLLAMA_MODEL must be set in environment variables")

        use_remote = (
            task in ("synthesis", "news_sentiment")
            and settings.ollama_remote_base_url
        )

        if use_remote:
            if self._remote_provider is None:
                remote_url = settings.ollama_remote_base_url
                if remote_url is None:
                    raise ValueError("OLLAMA_REMOTE_BASE_URL is not set")
                self._remote_provider = OllamaClient(
                    base_url=remote_url,
                    model=settings.ollama_model,
                )
            return self._remote_provider
        else:
            if self._local_provider is None:
                self._local_provider = OllamaClient(
                    base_url=settings.ollama_base_url,
                    model=settings.ollama_model,
                )
            return self._local_provider
