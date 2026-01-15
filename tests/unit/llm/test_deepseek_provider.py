from unittest.mock import Mock, patch

import httpx

from src.core.models.llm import LlmRequest
from src.core.ports.llm_provider import HealthCheckResult
from src.llm.deepseek.deepseek_client import DeepSeekClient


def test_deepseek_client_health_check_missing_api_key():
    client = DeepSeekClient(
        base_url="https://api.deepseek.com", api_key="", provider_name="deepseek_api"
    )
    result = client.health_check()

    assert isinstance(result, HealthCheckResult)
    assert result.ok is False
    assert "missing api key" in result.reason


def test_deepseek_client_health_check_success():
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = DeepSeekClient(
            base_url="https://api.deepseek.com", api_key="test-key", provider_name="deepseek_api"
        )
        result = client.health_check()

        assert isinstance(result, HealthCheckResult)
        assert result.ok is True
        assert result.reason == ""
        call_args = mock_client.get.call_args
        assert "Authorization" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-key"


def test_deepseek_client_health_check_failure():
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_client_class.return_value = mock_client

        client = DeepSeekClient(
            base_url="https://api.deepseek.com", api_key="test-key", provider_name="deepseek_api"
        )
        result = client.health_check()

        assert isinstance(result, HealthCheckResult)
        assert result.ok is False
        assert "Connection failed" in result.reason


def test_deepseek_client_generate_with_request_success():
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "test response"}}]}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client_class.return_value.__exit__.return_value = None

        client = DeepSeekClient(
            base_url="https://api.deepseek.com", api_key="test-key", provider_name="deepseek_api"
        )
        request = LlmRequest(
            task="test",
            system_prompt="system",
            user_prompt="user",
            temperature=0.2,
            timeout_seconds=60.0,
            max_retries=1,
            model_name="deepseek-chat",
        )

        response = client.generate_with_request(request)

        assert response.text == "test response"
        assert response.provider_name == "deepseek_api"
        assert response.model_name == "deepseek-chat"
        assert response.error is None
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["model"] == "deepseek-chat"
        assert call_args[1]["json"]["temperature"] == 0.2


def test_deepseek_client_generate_with_request_missing_api_key():
    client = DeepSeekClient(
        base_url="https://api.deepseek.com", api_key="", provider_name="deepseek_api"
    )
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
    assert response.error == "missing api key"


def test_deepseek_client_generate_with_request_handles_error():
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client.post.side_effect = httpx.RequestError("Network error")
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client_class.return_value.__exit__.return_value = None

        client = DeepSeekClient(
            base_url="https://api.deepseek.com", api_key="test-key", provider_name="deepseek_api"
        )
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


def test_deepseek_client_get_provider_name():
    client = DeepSeekClient(
        base_url="https://api.deepseek.com", api_key="test-key", provider_name="deepseek_api"
    )
    assert client.get_provider_name() == "deepseek_api"
