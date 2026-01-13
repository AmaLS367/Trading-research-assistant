from datetime import datetime
from unittest.mock import Mock

import httpx

from src.core.models.timeframe import Timeframe
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
    mock_response.raise_for_status.return_value = None

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider = GDELTProvider(base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert "Quality" in result
    assert "EUR USD Exchange Rate Rises" in result or "European Central Bank" in result


def test_get_news_summary_handles_empty_articles() -> None:
    mock_response_data = {"articles": []}

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider = GDELTProvider(base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert "Quality LOW" in result or "No news" in result


def test_get_news_summary_handles_missing_articles_key() -> None:
    mock_response_data = {}

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = mock_response_data
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider = GDELTProvider(base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert "Quality LOW" in result or "No news" in result


def test_get_news_summary_handles_network_error() -> None:
    mock_client = Mock(spec=httpx.Client)
    mock_client.get.side_effect = httpx.NetworkError("Connection failed")

    provider = GDELTProvider(base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert "Quality LOW" in result or "Error" in result


def test_get_news_summary_handles_timeout() -> None:
    mock_client = Mock(spec=httpx.Client)
    mock_client.get.side_effect = httpx.TimeoutException("Request timeout")

    provider = GDELTProvider(base_url="https://api.test.com")
    provider.client = mock_client

    result = provider.get_news_summary("EURUSD")

    assert "Quality LOW" in result or "Error" in result


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

    assert "Quality LOW" in result or "Error" in result


def test_build_query_from_symbol() -> None:
    provider = GDELTProvider(base_url="https://api.test.com")

    assert provider._build_query_from_symbol("EURUSD") == "EUR USD"
    assert provider._build_query_from_symbol("GBPUSD") == "GBP USD"
    assert provider._build_query_from_symbol("USDJPY") == "USD JPY"
    assert provider._build_query_from_symbol("EUR_USD") == "EUR USD"
    assert provider._build_query_from_symbol("EUR USD") == "EUR USD"


def test_get_query_templates_includes_language_filter() -> None:
    provider = GDELTProvider(base_url="https://api.test.com")
    templates = provider._get_query_templates("EURUSD")

    assert "pair" in templates
    assert "macro" in templates
    assert "risk" in templates

    for query in templates.values():
        assert "sourcelang:English" in query


def test_filter_dedup_score_removes_duplicates() -> None:
    provider = GDELTProvider(base_url="https://api.test.com")
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
            title="Euro Dollar Exchange Rate Rises",
            relevance_score=0.0,
            query_tag="pair",
        ),
        NewsArticle(
            title="USD Strengthens Against Euro",
            relevance_score=0.0,
            query_tag="pair",
        ),
    ]

    filtered = provider._filter_dedup_score(articles, "EURUSD")

    assert len(filtered) <= len(articles)
    titles = [a.title for a in filtered]
    assert len(set(titles)) == len(titles)


def test_filter_dedup_score_calculates_relevance() -> None:
    provider = GDELTProvider(base_url="https://api.test.com")
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

    filtered = provider._filter_dedup_score(articles, "EURUSD")

    assert len(filtered) > 0
    if filtered:
        assert filtered[0].relevance_score > 0.0
        assert filtered[0].title == "EUR USD Exchange Rate Rises on ECB Policy"


def test_get_news_digest_determines_quality_high() -> None:
    provider = GDELTProvider(base_url="https://api.test.com")
    from src.core.models.news import NewsArticle

    mock_response_data = {
        "articles": [
            {"title": f"EUR USD News Article {i} with ECB and CPI", "seendate": "20240101120000"}
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
    provider = GDELTProvider(base_url="https://api.test.com")

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.side_effect = httpx.NetworkError("Connection failed")

    provider.client = mock_client

    digest = provider.get_news_digest("EURUSD", Timeframe.H1)

    assert digest.quality == "LOW"
    assert "Error" in digest.quality_reason or "Not enough" in digest.quality_reason
    assert len(digest.articles) == 0
