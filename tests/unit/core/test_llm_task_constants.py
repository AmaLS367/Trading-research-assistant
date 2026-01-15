from src.core.ports.llm_provider_name import (
    ALL_PROVIDERS,
    PROVIDER_DEEPSEEK_API,
    PROVIDER_OLLAMA_LOCAL,
    PROVIDER_OLLAMA_SERVER,
)
from src.core.ports.llm_tasks import (
    ALL_TASKS,
    TASK_NEWS_ANALYSIS,
    TASK_SYNTHESIS,
    TASK_TECH_ANALYSIS,
    TASK_VERIFICATION,
)


def test_task_constants_values():
    assert TASK_TECH_ANALYSIS == "tech_analysis"
    assert TASK_NEWS_ANALYSIS == "news_analysis"
    assert TASK_SYNTHESIS == "synthesis"
    assert TASK_VERIFICATION == "verification"


def test_all_tasks_contains_all_constants():
    assert TASK_TECH_ANALYSIS in ALL_TASKS
    assert TASK_NEWS_ANALYSIS in ALL_TASKS
    assert TASK_SYNTHESIS in ALL_TASKS
    assert TASK_VERIFICATION in ALL_TASKS
    assert len(ALL_TASKS) == 4


def test_provider_constants_values():
    assert PROVIDER_OLLAMA_LOCAL == "ollama_local"
    assert PROVIDER_OLLAMA_SERVER == "ollama_server"
    assert PROVIDER_DEEPSEEK_API == "deepseek_api"


def test_all_providers_contains_all_constants():
    assert PROVIDER_OLLAMA_LOCAL in ALL_PROVIDERS
    assert PROVIDER_OLLAMA_SERVER in ALL_PROVIDERS
    assert PROVIDER_DEEPSEEK_API in ALL_PROVIDERS
    assert len(ALL_PROVIDERS) == 3
