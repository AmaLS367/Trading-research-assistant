from types import SimpleNamespace
from unittest.mock import patch

from src.app.settings import get_settings
from src.app.wiring import create_llm_router
from src.core.ports.llm_provider_name import PROVIDER_OLLAMA_LOCAL
from src.core.ports.llm_tasks import TASK_TECH_ANALYSIS


def test_wiring_injects_default_route_for_strict_mode_without_candidates():
    class IsolatedSettings:
        llm_router_mode = "strict"
        llm_verifier_enabled = False
        llm_max_retries = 1
        llm_timeout_seconds = 60.0
        llm_temperature = 0.2
        ollama_model = "llama3:test-model"

        def get_task_candidates(self, task_name: str) -> list[object]:
            return []

        @property
        def llm_last_resort(self) -> SimpleNamespace:
            return SimpleNamespace(provider=PROVIDER_OLLAMA_LOCAL, model=self.ollama_model)

    isolated_settings = IsolatedSettings()
    get_settings.cache_clear()
    with (
        patch("src.app.wiring.get_settings", return_value=isolated_settings),
        patch("src.app.wiring.settings", isolated_settings),
        patch("src.app.wiring.create_llm_providers", return_value={}),
    ):
        router = create_llm_router()

    routing = router.task_routings[TASK_TECH_ANALYSIS]

    assert routing.steps
    assert routing.steps[0].provider == PROVIDER_OLLAMA_LOCAL
    assert routing.steps[0].model == "llama3:test-model"

    get_settings.cache_clear()
