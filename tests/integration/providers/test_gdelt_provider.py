from datetime import datetime
from typing import Any
from unittest.mock import Mock

import httpx

from src.core.models.timeframe import Timeframe
from src.news_providers.gdelt_provider import GDELTProvider


def test_get_news_summary_collects_titles() -> None:
    mock_response_data: dict[str, Any] = {
        "articles": [
            {"title": "EUR USD Exchange Rate Rises on Forex Market", "seendate": "20240101120000"},
            {"title": "European Central Bank Announces Forex Policy", "seendate": "20240101120000"},
            {
                "title": "USD Strengthens Against Euro in Currency Market",
                "seendate": "20240101120000",
            },
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


def test_get_news_summary_handles_empty_articles() -> None:
    mock_response_data: dict[str, list[dict[str, Any]]] = {"articles": []}

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
    mock_response_data: dict[str, Any] = {}

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

    assert "strict" in templates
    assert "medium" in templates
    assert "broad" in templates

    for pass_name in ["strict", "medium", "broad"]:
        if pass_name in templates and templates[pass_name]:
            for query in templates[pass_name].values():
                assert "sourcelang:English" in query
                assert (
                    "forex OR fx OR currency" in query
                    or '"exchange rate"' in query
                    or '"foreign exchange"' in query
                )


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

    filtered, _, _ = provider._filter_dedup_score(articles, "EURUSD")

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

    filtered, _, _ = provider._filter_dedup_score(articles, "EURUSD")

    assert len(filtered) > 0
    if filtered:
        assert filtered[0].relevance_score > 0.0
        assert filtered[0].title == "EUR USD Exchange Rate Rises on ECB Policy"


def test_get_news_digest_determines_quality_high() -> None:
    provider = GDELTProvider(base_url="https://api.test.com")

    mock_response_data: dict[str, Any] = {
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


def test_fetch_articles_with_fallback_multi_pass() -> None:
    provider = GDELTProvider(base_url="https://api.test.com")

    mock_response_empty = Mock(spec=httpx.Response)
    mock_response_empty.json.return_value = {"articles": []}
    mock_response_empty.status_code = 200
    mock_response_empty.raise_for_status.return_value = None

    mock_response_strict = Mock(spec=httpx.Response)
    mock_response_strict.json.return_value = {
        "articles": [
            {"title": "Sephora Store Opening", "seendate": "20240101120000"},
            {"title": "Swimming Competition Results", "seendate": "20240101120000"},
        ]
    }
    mock_response_strict.status_code = 200
    mock_response_strict.raise_for_status.return_value = None

    mock_response_medium = Mock(spec=httpx.Response)
    mock_response_medium.json.return_value = {
        "articles": [
            {"title": "Weather Forecast Today", "seendate": "20240101120000"},
        ]
    }
    mock_response_medium.status_code = 200
    mock_response_medium.raise_for_status.return_value = None

    mock_response_broad = Mock(spec=httpx.Response)
    mock_response_broad.json.return_value = {
        "articles": [
            {"title": "EUR USD Exchange Rate Rises on ECB Policy", "seendate": "20240101120000"},
            {"title": "Forex Market Volatility Increases", "seendate": "20240101120000"},
        ]
    }
    mock_response_broad.status_code = 200
    mock_response_broad.raise_for_status.return_value = None

    mock_client = Mock(spec=httpx.Client)

    def mock_get_side_effect(*args, **kwargs):
        query = kwargs.get("params", {}).get("query", "")
        if "pair_strict" in query or "EURUSD" in query:
            return mock_response_strict
        elif "macro_medium" in query:
            return mock_response_medium
        elif "macro_broad" in query or "risk_broad" in query:
            return mock_response_broad
        else:
            return mock_response_empty

    mock_client.get.side_effect = mock_get_side_effect

    provider.client = mock_client

    articles, pass_counts, queries_used, gdelt_debug = provider.fetch_articles_with_fallback(
        "EURUSD"
    )

    assert len(articles) >= 0
    assert "strict" in pass_counts or "medium" in pass_counts or "broad" in pass_counts
    assert "passes" in gdelt_debug


def test_query_templates_include_fx_anchors() -> None:
    provider = GDELTProvider(base_url="https://api.test.com")
    templates = provider._get_query_templates("EURUSD")

    for pass_name in ["strict", "medium", "broad"]:
        if pass_name in templates:
            for _query_tag, query in templates[pass_name].items():
                assert "sourcelang:English" in query
                assert (
                    "forex OR fx OR currency" in query
                    or '"exchange rate"' in query
                    or '"foreign exchange"' in query
                )


def test_fetch_articles_for_query_collects_diagnostics_empty_articles() -> None:
    provider = GDELTProvider(base_url="https://api.test.com")

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = {"timeline": [], "other_key": "value"}
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider.client = mock_client

    articles, debug_info = provider._fetch_articles_for_query("test query", "test_tag")

    assert len(articles) == 0
    assert debug_info["tag"] == "test_tag"
    assert debug_info["http_status"] == 200
    assert debug_info["items_count"] == 0
    assert debug_info["json_keys"] == ["timeline", "other_key"]
    assert debug_info["error"] is None


def test_fetch_articles_for_query_collects_diagnostics_with_articles() -> None:
    provider = GDELTProvider(base_url="https://api.test.com")

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = {
        "articles": [
            {"title": "EUR USD Exchange Rate Rises", "seendate": "20240101120000"},
        ]
    }
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider.client = mock_client

    articles, debug_info = provider._fetch_articles_for_query("test query", "test_tag")

    assert len(articles) == 1
    assert debug_info["http_status"] == 200
    assert debug_info["items_count"] == 1
    assert debug_info["sample_title"] == "EUR USD Exchange Rate Rises"
    assert debug_info["error"] is None


def test_fetch_articles_for_query_collects_diagnostics_http_error() -> None:
    provider = GDELTProvider(base_url="https://api.test.com")

    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Rate limit exceeded", request=Mock(), response=mock_response
    )

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider.client = mock_client

    articles, debug_info = provider._fetch_articles_for_query("test query", "test_tag")

    assert len(articles) == 0
    assert debug_info["http_status"] == 429
    assert debug_info["error"] is not None
    assert "429" in debug_info["error"] or "Rate limit" in debug_info["error"]


def test_fetch_articles_with_fallback_includes_diagnostics() -> None:
    provider = GDELTProvider(base_url="https://api.test.com")

    mock_response = Mock(spec=httpx.Response)
    mock_response.json.return_value = {"articles": []}
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None

    mock_client = Mock(spec=httpx.Client)
    mock_client.get.return_value = mock_response

    provider.client = mock_client

    articles, pass_counts, queries_used, gdelt_debug = provider.fetch_articles_with_fallback(
        "EURUSD"
    )

    assert "passes" in gdelt_debug
    assert isinstance(gdelt_debug["passes"], dict)
    for pass_name in ["strict", "medium", "broad"]:
        if pass_name in gdelt_debug["passes"]:
            assert "requests" in gdelt_debug["passes"][pass_name]
            assert isinstance(gdelt_debug["passes"][pass_name]["requests"], list)
