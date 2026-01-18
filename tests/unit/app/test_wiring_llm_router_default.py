import os
from unittest.mock import patch

from src.app.settings import get_settings
from src.app.wiring import create_llm_router
from src.core.ports.llm_provider_name import PROVIDER_OLLAMA_LOCAL
from src.core.ports.llm_tasks import TASK_TECH_ANALYSIS


def test_wiring_injects_default_route_for_strict_mode_without_candidates():
    with patch.dict(
        os.environ,
        {
            "LLM_ROUTER_MODE": "strict",
            "OLLAMA_MODEL": "llama3:test-model",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        router = create_llm_router()

        routing = router.task_routings[TASK_TECH_ANALYSIS]

        assert routing.steps
        assert routing.steps[0].provider == PROVIDER_OLLAMA_LOCAL
        assert routing.steps[0].model == "llama3:test-model"

    get_settings.cache_clear()
