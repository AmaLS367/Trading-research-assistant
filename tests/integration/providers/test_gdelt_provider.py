from unittest.mock import Mock

import httpx

from src.news_providers.gdelt_provider import GDELTProvider


def test_get_news_summary_collects_titles() -> None:
    mock_response_data = {
        "articles": [
            {"title": "EUR USD Exchange Rate Rises"},
            {"title": "European Central Bank Announces Policy"},
            {"title": "USD Strengthens Against Euro"},
        ]
    }

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider = GDELTProvider(base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert result.startswith("Latest news:")
    assert "- EUR USD Exchange Rate Rises" in result
    assert "- European Central Bank Announces Policy" in result
    assert "- USD Strengthens Against Euro" in result

    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert call_args.kwargs["params"]["query"] == "EUR USD"
    assert call_args.kwargs["params"]["mode"] == "artlist"
    assert call_args.kwargs["params"]["format"] == "json"
    assert call_args.kwargs["params"]["maxrecords"] == 5
    assert call_args.kwargs["params"]["timespan"] == "24h"
    assert call_args.kwargs["params"]["sort"] == "datedesc"


def test_get_news_summary_handles_empty_articles() -> None:
    mock_response_data = {"articles": []}

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider = GDELTProvider(base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert result == "No news found via GDELT."


def test_get_news_summary_handles_missing_articles_key() -> None:
    mock_response_data = {}

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider = GDELTProvider(base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert result == "No news found via GDELT."


def test_get_news_summary_handles_network_error() -> None:
    mock_client = Mock(spec=httpx.Client)
    mock_client.get.side_effect = httpx.NetworkError("Connection failed")

    provider = GDELTProvider(base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert result == "No news found via GDELT."


def test_get_news_summary_handles_timeout() -> None:
    mock_client = Mock(spec=httpx.Client)
    mock_client.get.side_effect = httpx.TimeoutException("Request timeout")

    provider = GDELTProvider(base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert result == "No news found via GDELT."


def test_get_news_summary_handles_http_error() -> None:
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error", request=Mock(), response=mock_response
    )

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider = GDELTProvider(base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert result == "No news found via GDELT."


def test_build_query_from_symbol() -> None:
    provider = GDELTProvider(base_url="https://api.test.com")

    assert provider._build_query_from_symbol("EURUSD") == "EUR USD"
    assert provider._build_query_from_symbol("GBPUSD") == "GBP USD"
    assert provider._build_query_from_symbol("USDJPY") == "USD JPY"
    assert provider._build_query_from_symbol("EUR_USD") == "EUR USD"
    assert provider._build_query_from_symbol("EUR USD") == "EUR USD"
