import os
from unittest.mock import patch

from src.app.settings import get_settings


def test_new_env_keys_present():
    env_vars = {
        "OLLAMA_LOCAL_URL": "http://localhost:11434",
        "OLLAMA_SERVER_URL": "http://server:11434",
        "DEEPSEEK_API_KEY": "test-key",
        "DEEPSEEK_API_BASE": "https://api.deepseek.com",
        "TECH_PRIMARY_PROVIDER": "deepseek_api",
        "TECH_PRIMARY_MODEL": "deepseek-chat",
        "TECH_FALLBACK1_PROVIDER": "ollama_server",
        "TECH_FALLBACK1_MODEL": "qwen2.5:32b",
        "TECH_FALLBACK2_PROVIDER": "",
        "TECH_FALLBACK2_MODEL": "",
        "OLLAMA_MODEL": "",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.ollama_local_url == "http://localhost:11434"
        assert settings.ollama_server_url == "http://server:11434"
        assert settings.deepseek_api_key == "test-key"
        assert settings.deepseek_api_base == "https://api.deepseek.com"

        tech_routing = settings.get_tech_routing()
        assert len(tech_routing.steps) >= 2
        assert tech_routing.steps[0].provider == "deepseek_api"
        assert tech_routing.steps[0].model == "deepseek-chat"
        assert tech_routing.steps[1].provider == "ollama_server"
        assert tech_routing.steps[1].model == "qwen2.5:32b"

    get_settings.cache_clear()


def test_legacy_keys_only(monkeypatch):
    keys_to_remove = [
        "OLLAMA_LOCAL_URL",
        "OLLAMA_SERVER_URL",
    ]
    for key in keys_to_remove:
        monkeypatch.delenv(key, raising=False)

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.ollama_base_url is not None
    assert settings.ollama_model is not None or settings.ollama_model == ""
    assert settings._get_ollama_local_url() == settings.ollama_base_url

    tech_routing = settings.get_tech_routing()
    assert len(tech_routing.steps) >= 1

    get_settings.cache_clear()


def test_empty_deepseek_api_key():
    with patch.dict(
        os.environ,
        {
            "DEEPSEEK_API_KEY": "",
            "DEEPSEEK_API_BASE": "https://api.deepseek.com",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.deepseek_api_key is None
        assert settings.deepseek_api_base == "https://api.deepseek.com"

    get_settings.cache_clear()


def test_invalid_url_normalized_to_none():
    with patch.dict(
        os.environ,
        {
            "OLLAMA_LOCAL_URL": "not-a-url",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.ollama_local_url is None

    get_settings.cache_clear()


def test_fallback3_support():
    env_vars = {
        "TECH_PRIMARY_PROVIDER": "deepseek_api",
        "TECH_PRIMARY_MODEL": "deepseek-chat",
        "TECH_FALLBACK1_PROVIDER": "ollama_server",
        "TECH_FALLBACK1_MODEL": "qwen2.5:32b",
        "TECH_FALLBACK2_PROVIDER": "ollama_local",
        "TECH_FALLBACK2_MODEL": "llama3:latest",
        "TECH_FALLBACK3_PROVIDER": "ollama_local",
        "TECH_FALLBACK3_MODEL": "mistral:latest",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        get_settings.cache_clear()
        settings = get_settings()

        tech_routing = settings.get_tech_routing()
        assert len(tech_routing.steps) == 4
        assert tech_routing.steps[0].provider == "deepseek_api"
        assert tech_routing.steps[0].model == "deepseek-chat"
        assert tech_routing.steps[1].provider == "ollama_server"
        assert tech_routing.steps[1].model == "qwen2.5:32b"
        assert tech_routing.steps[2].provider == "ollama_local"
        assert tech_routing.steps[2].model == "llama3:latest"
        assert tech_routing.steps[3].provider == "ollama_local"
        assert tech_routing.steps[3].model == "mistral:latest"

    get_settings.cache_clear()


def test_routing_config():
    with patch.dict(
        os.environ,
        {
            "LLM_ROUTER_MODE": "sequential",
            "LLM_VERIFIER_ENABLED": "true",
            "LLM_MAX_RETRIES": "5",
            "LLM_TIMEOUT_SECONDS": "120.0",
            "LLM_TEMPERATURE": "0.5",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        settings = get_settings()

        config = settings.get_llm_routing_config()
        assert config.router_mode == "sequential"
        assert config.verifier_enabled is True
        assert config.max_retries == 5
        assert config.timeout_seconds == 120.0
        assert config.temperature == 0.5

    get_settings.cache_clear()
