from unittest.mock import Mock, patch

import httpx

from src.core.models.llm import LlmRequest
from src.core.ports.llm_provider import HealthCheckResult
from src.llm.ollama.ollama_client import OllamaClient


def test_ollama_client_health_check_success():
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = OllamaClient(base_url="http://localhost:11434", provider_name="ollama_local")
        result = client.health_check()

        assert isinstance(result, HealthCheckResult)
        assert result.ok is True
        assert result.reason == ""
        mock_client.get.assert_called_once_with("http://localhost:11434/api/tags", timeout=5.0)


def test_ollama_client_health_check_failure():
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_client_class.return_value = mock_client

        client = OllamaClient(base_url="http://localhost:11434", provider_name="ollama_local")
        result = client.health_check()

        assert isinstance(result, HealthCheckResult)
        assert result.ok is False
        assert "Connection failed" in result.reason


def test_ollama_client_generate_with_request_uses_model_from_request():
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test response"}}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client_class.return_value.__exit__.return_value = None

        client = OllamaClient(
            base_url="http://localhost:11434", model="default-model", provider_name="ollama_local"
        )
        request = LlmRequest(
            task="test",
            system_prompt="system",
            user_prompt="user",
            temperature=0.2,
            timeout_seconds=60.0,
            max_retries=1,
            model_name="request-model",
        )

        response = client.generate_with_request(request)

        assert response.model_name == "request-model"
        assert response.text == "test response"
        assert response.provider_name == "ollama_local"
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["model"] == "request-model"


def test_ollama_client_generate_with_request_uses_default_model():
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test response"}}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client_class.return_value.__exit__.return_value = None

        client = OllamaClient(
            base_url="http://localhost:11434", model="default-model", provider_name="ollama_local"
        )
        request = LlmRequest(
            task="test",
            system_prompt="system",
            user_prompt="user",
            temperature=0.2,
            timeout_seconds=60.0,
            max_retries=1,
            model_name=None,
        )

        response = client.generate_with_request(request)

        assert response.model_name == "default-model"
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["model"] == "default-model"


def test_ollama_client_generate_with_request_handles_error():
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.post.side_effect = httpx.RequestError("Network error")
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client_class.return_value.__exit__.return_value = None

        client = OllamaClient(base_url="http://localhost:11434", provider_name="ollama_local")
        request = LlmRequest(
            task="test",
            system_prompt="system",
            user_prompt="user",
            temperature=0.2,
            timeout_seconds=60.0,
            max_retries=1,
        )

        response = client.generate_with_request(request)

        assert response.text == ""
        assert response.error is not None
        assert "Network error" in response.error


def test_ollama_client_get_provider_name():
    client = OllamaClient(
        base_url="http://localhost:11434", provider_name="ollama_server", model="test"
    )
    assert client.get_provider_name() == "ollama_server"
