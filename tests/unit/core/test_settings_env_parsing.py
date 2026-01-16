import os
from pathlib import Path
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


def test_logging_settings_parsing():
    env_vars = {
        "LOG_DIR": "custom_logs",
        "LOG_LEVEL": "DEBUG",
        "LOG_CONSOLE_LEVEL": "WARNING",
        "LOG_FORMAT": "text",
        "LOG_ROTATION": "12:00",
        "LOG_RETENTION": "60 days",
        "LOG_COMPRESSION": "gz",
        "LOG_MASK_AUTH": "false",
        "LOG_HTTP_LEVEL": "ERROR",
        "LOG_SPLIT_FILES": "false",
        "LOG_ENABLE_HTTP_FILE": "true",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        get_settings.cache_clear()
        settings = get_settings()

        assert str(settings.log_dir) == "custom_logs"
        assert settings.log_level == "DEBUG"
        assert settings.log_console_level == "WARNING"
        assert settings.log_format == "text"
        assert settings.log_rotation == "12:00"
        assert settings.log_retention == "60 days"
        assert settings.log_compression == "gz"
        assert settings.log_mask_auth is False
        assert settings.log_http_level == "ERROR"
        assert settings.log_split_files is False
        assert settings.log_enable_http_file is True

    get_settings.cache_clear()


def test_logging_settings_defaults():
    # Test that logging settings have reasonable defaults
    # Note: actual defaults may be affected by .env file, so we just verify they exist
    get_settings.cache_clear()
    settings = get_settings()

    assert str(settings.log_dir) == str(Path("logs"))
    assert settings.log_level in ("INFO", "DEBUG", "WARNING")
    assert settings.log_console_level in ("INFO", "DEBUG", "WARNING")
    assert settings.log_format in ("json", "text")
    assert settings.log_rotation is not None
    assert settings.log_retention is not None
    assert settings.log_compression in ("zip", "gz", "tar.gz")
    assert isinstance(settings.log_mask_auth, bool)
    assert settings.log_http_level in ("WARNING", "ERROR", "INFO")
    assert isinstance(settings.log_split_files, bool)
    assert isinstance(settings.log_enable_http_file, bool)

    get_settings.cache_clear()


def test_ollama_server_url_placeholder_rejected():
    with patch.dict(
        os.environ,
        {
            "OLLAMA_SERVER_URL": "http://your-server-ip:11434",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.ollama_server_url is None

    get_settings.cache_clear()


def test_ollama_server_url_localhost_rejected():
    with patch.dict(
        os.environ,
        {
            "OLLAMA_SERVER_URL": "http://127.0.0.1:11434",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.ollama_server_url is None

    get_settings.cache_clear()


def test_ollama_server_url_valid_ipv4_accepted():
    with patch.dict(
        os.environ,
        {
            "OLLAMA_SERVER_URL": "http://123.45.67.89:11434",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.ollama_server_url == "http://123.45.67.89:11434"

    get_settings.cache_clear()


def test_ollama_server_url_valid_domain_accepted():
    with patch.dict(
        os.environ,
        {
            "OLLAMA_SERVER_URL": "https://api.myserver.com:11434",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.ollama_server_url == "https://api.myserver.com:11434"

    get_settings.cache_clear()


def test_new_routing_schema_local():
    env_vars = {
        "RUNTIME_ENV": "local",
        "TECH_LOCAL_PRIMARY_PROVIDER": "ollama_local",
        "TECH_LOCAL_PRIMARY_MODEL": "llama3:latest",
        "TECH_LOCAL_FALLBACK1_PROVIDER": "deepseek_api",
        "TECH_LOCAL_FALLBACK1_MODEL": "deepseek-chat",
        "LLM_LAST_RESORT_PROVIDER": "ollama_local",
        "LLM_LAST_RESORT_MODEL": "llama3:latest",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.runtime_env == "local"
        candidates = settings.get_task_candidates("tech_analysis")
        assert len(candidates) == 2
        assert candidates[0].provider == "ollama_local"
        assert candidates[0].model == "llama3:latest"
        assert candidates[1].provider == "deepseek_api"
        assert candidates[1].model == "deepseek-chat"

        last_resort = settings.llm_last_resort
        assert last_resort.provider == "ollama_local"
        assert last_resort.model == "llama3:latest"

    get_settings.cache_clear()


def test_new_routing_schema_server():
    env_vars = {
        "RUNTIME_ENV": "server",
        "TECH_SERVER_PRIMARY_PROVIDER": "ollama_server",
        "TECH_SERVER_PRIMARY_MODEL": "qwen2.5:32b",
        "TECH_SERVER_FALLBACK1_PROVIDER": "deepseek_api",
        "TECH_SERVER_FALLBACK1_MODEL": "deepseek-chat",
        "LLM_LAST_RESORT_PROVIDER": "ollama_local",
        "LLM_LAST_RESORT_MODEL": "llama3:latest",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        get_settings.cache_clear()
        settings = get_settings()

        assert settings.runtime_env == "server"
        candidates = settings.get_task_candidates("tech_analysis")
        assert len(candidates) == 2
        assert candidates[0].provider == "ollama_server"
        assert candidates[0].model == "qwen2.5:32b"
        assert candidates[1].provider == "deepseek_api"
        assert candidates[1].model == "deepseek-chat"

    get_settings.cache_clear()


def test_backward_compatibility_old_schema():
    env_vars = {
        "TECH_PRIMARY_PROVIDER": "deepseek_api",
        "TECH_PRIMARY_MODEL": "deepseek-chat",
        "TECH_FALLBACK1_PROVIDER": "ollama_local",
        "TECH_FALLBACK1_MODEL": "llama3:latest",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "TECH_LOCAL_PRIMARY_PROVIDER": "",
        "TECH_SERVER_PRIMARY_PROVIDER": "",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        get_settings.cache_clear()
        settings = get_settings()

        candidates = settings.get_task_candidates("tech_analysis")
        assert len(candidates) >= 2
        assert candidates[0].provider == "deepseek_api"
        assert candidates[0].model == "deepseek-chat"
        assert any(c.provider == "ollama_local" and c.model == "llama3:latest" for c in candidates)

    get_settings.cache_clear()


def test_last_resort_default():
    with patch.dict(os.environ, {}, clear=False):
        get_settings.cache_clear()
        settings = get_settings()

        last_resort = settings.llm_last_resort
        assert last_resort.provider == "ollama_local"
        assert last_resort.model == "llama3:latest"

    get_settings.cache_clear()
