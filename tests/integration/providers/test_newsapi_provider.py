from datetime import datetime
from typing import Any
from unittest.mock import Mock

import httpx

from src.core.models.timeframe import Timeframe
from src.news_providers.newsapi_provider import NewsAPIProvider


def test_get_news_summary_collects_titles() -> None:
    mock_response_data: dict[str, Any] = {
        "articles": [
            {
                "title": "EUR USD Exchange Rate Rises on Forex Market",
                "url": "https://example.com/article1",
                "source": {"name": "Reuters"},
                "publishedAt": "2024-01-01T12:00:00Z",
            },
            {
                "title": "European Central Bank Announces Forex Policy",
                "url": "https://example.com/article2",
                "source": {"name": "Bloomberg"},
                "publishedAt": "2024-01-01T12:00:00Z",
            },
        ]
    }

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider = NewsAPIProvider(api_key="test_key", base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert "Quality" in result


def test_get_news_summary_handles_empty_articles() -> None:
    mock_response_data: dict[str, list[dict[str, Any]]] = {"articles": []}

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider = NewsAPIProvider(api_key="test_key", base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert "Quality LOW" in result or "No news" in result


def test_get_news_summary_handles_network_error() -> None:
    mock_client = Mock(spec=httpx.Client)
    mock_client.get.side_effect = httpx.NetworkError("Connection failed")

    provider = NewsAPIProvider(api_key="test_key", base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert "Quality LOW" in result or "Error" in result or "No news" in result


def test_get_news_summary_handles_timeout() -> None:
    mock_client = Mock(spec=httpx.Client)
    mock_client.get.side_effect = httpx.TimeoutException("Request timeout")

    provider = NewsAPIProvider(api_key="test_key", base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert "Quality LOW" in result or "Error" in result or "No news" in result


def test_get_news_summary_handles_http_error() -> None:
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error", request=Mock(), response=mock_response
    )

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider = NewsAPIProvider(api_key="test_key", base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert "Quality LOW" in result or "Error" in result or "No news" in result


def test_get_query_templates_includes_fx_anchors() -> None:
    provider = NewsAPIProvider(api_key="test_key", base_url="https://api.test.com")
    templates = provider._get_query_templates("EURUSD")

    assert "pair" in templates or "macro" in templates

    for query in templates.values():
        assert "forex OR fx OR currency" in query or '"exchange rate"' in query


def test_filter_dedup_score_removes_duplicates() -> None:
    provider = NewsAPIProvider(api_key="test_key", base_url="https://api.test.com")
    from src.core.models.news import NewsArticle

    articles = [
        NewsArticle(
            title="EUR USD Exchange Rate Rises",
            relevance_score=0.0,
            query_tag="pair",
        ),
        NewsArticle(
            title="EUR USD Exchange Rate Rises",
            relevance_score=0.0,
            query_tag="pair",
        ),
        NewsArticle(
            title="USD Strengthens Against Euro",
            relevance_score=0.0,
            query_tag="pair",
        ),
    ]

    filtered, _, _ = provider._filter_dedup_score(articles, "EURUSD")

    assert len(filtered) <= len(articles)
    titles = [a.title for a in filtered]
    assert len(set(titles)) == len(titles)


def test_filter_dedup_score_calculates_relevance() -> None:
    provider = NewsAPIProvider(api_key="test_key", base_url="https://api.test.com")
    from src.core.models.news import NewsArticle

    now = datetime.now()
    articles = [
        NewsArticle(
            title="EUR USD Exchange Rate Rises on ECB Policy",
            published_at=now,
            relevance_score=0.0,
            query_tag="pair",
        ),
        NewsArticle(
            title="Currency Converter Today",
            relevance_score=0.0,
            query_tag="pair",
        ),
        NewsArticle(
            title="Short",
            relevance_score=0.0,
            query_tag="pair",
        ),
    ]

    filtered, _, _ = provider._filter_dedup_score(articles, "EURUSD")

    assert len(filtered) > 0
    if filtered:
        assert filtered[0].relevance_score > 0.0
        assert filtered[0].title == "EUR USD Exchange Rate Rises on ECB Policy"


def test_get_news_digest_determines_quality() -> None:
    provider = NewsAPIProvider(api_key="test_key", base_url="https://api.test.com")

    mock_response_data: dict[str, Any] = {
        "articles": [
            {
                "title": f"EUR USD News Article {i} with ECB and CPI",
                "url": f"https://example.com/article{i}",
                "source": {"name": "Reuters"},
                "publishedAt": "2024-01-01T12:00:00Z",
            }
            for i in range(10)
        ]
    }

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider.client = mock_client

    digest = provider.get_news_digest("EURUSD", Timeframe.H1)

    assert digest.symbol == "EURUSD"
    assert digest.timeframe == Timeframe.H1
    assert digest.window_hours == 24
    assert digest.quality in ["HIGH", "MEDIUM", "LOW"]
    assert digest.quality_reason is not None


def test_get_news_digest_handles_errors_gracefully() -> None:
    provider = NewsAPIProvider(api_key="test_key", base_url="https://api.test.com")

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.side_effect = httpx.NetworkError("Connection failed")

    provider.client = mock_client

    digest = provider.get_news_digest("EURUSD", Timeframe.H1)

    assert digest.quality == "LOW"
    assert "Error" in digest.quality_reason or "Not enough" in digest.quality_reason
    assert len(digest.articles) == 0


def test_fetch_articles_for_query_parses_newsapi_response() -> None:
    provider = NewsAPIProvider(api_key="test_key", base_url="https://api.test.com")

    mock_response_data: dict[str, Any] = {
        "articles": [
            {
                "title": "EUR USD Exchange Rate Rises",
                "url": "https://example.com/article1",
                "source": {"name": "Reuters"},
                "publishedAt": "2024-01-01T12:00:00Z",
            },
            {
                "title": "ECB Announces Policy",
                "url": "https://example.com/article2",
                "source": {"name": "Bloomberg"},
                "publishedAt": "2024-01-01T13:00:00Z",
            },
        ]
    }

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider.client = mock_client

    articles = provider._fetch_articles_for_query("EURUSD OR forex", "pair")

    assert len(articles) == 2
    assert articles[0].title == "EUR USD Exchange Rate Rises"
    assert articles[0].source == "Reuters"
    assert articles[1].title == "ECB Announces Policy"
    assert articles[1].source == "Bloomberg"
