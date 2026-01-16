from unittest.mock import patch

from src.app.settings import get_settings, settings
from src.app.wiring import create_llm_providers
from src.core.ports.llm_provider_name import PROVIDER_OLLAMA_SERVER


def test_wiring_skips_disabled_ollama_server():
    with patch.dict(
        {"OLLAMA_SERVER_URL": "http://your-server-ip:11434"},
        clear=False,
    ):
        get_settings.cache_clear()
        providers = create_llm_providers()

        assert PROVIDER_OLLAMA_SERVER not in providers

    get_settings.cache_clear()


