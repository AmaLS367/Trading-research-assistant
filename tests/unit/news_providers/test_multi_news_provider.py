from unittest.mock import Mock

from src.core.models.news import NewsArticle, NewsDigest
from src.core.models.timeframe import Timeframe
from src.news_providers.multi_news_provider import MultiNewsProvider


def test_multi_provider_uses_primary_when_medium() -> None:
    primary = Mock()
    secondary = Mock()

    primary_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[
            NewsArticle(
                title="EUR USD Exchange Rate Rises",
                relevance_score=0.6,
                query_tag="pair",
            ),
            NewsArticle(
                title="ECB Announces Policy",
                relevance_score=0.6,
                query_tag="macro",
            ),
        ],
        quality="MEDIUM",
        quality_reason="Found 2 highly relevant articles",
        articles_after_filter=2,
    )

    primary.get_news_digest.return_value = primary_digest

    multi_provider = MultiNewsProvider(primary=primary, secondary=secondary)

    result = multi_provider.get_news_digest("EURUSD", Timeframe.H1)

    assert result.provider_used == "GDELT"
    assert result.quality == "MEDIUM"
    assert result.primary_quality == "MEDIUM"
    assert result.primary_reason == "Found 2 highly relevant articles"
    primary.get_news_digest.assert_called_once_with("EURUSD", Timeframe.H1)
    secondary.get_news_digest.assert_not_called()


def test_multi_provider_uses_primary_when_high() -> None:
    primary = Mock()
    secondary = Mock()

    primary_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[
            NewsArticle(title=f"Article {i}", relevance_score=0.6, query_tag="pair")
            for i in range(5)
        ],
        quality="HIGH",
        quality_reason="Found 5 highly relevant articles",
        articles_after_filter=5,
    )

    primary.get_news_digest.return_value = primary_digest

    multi_provider = MultiNewsProvider(primary=primary, secondary=secondary)

    result = multi_provider.get_news_digest("EURUSD", Timeframe.H1)

    assert result.provider_used == "GDELT"
    assert result.quality == "HIGH"
    primary.get_news_digest.assert_called_once()
    secondary.get_news_digest.assert_not_called()


def test_multi_provider_fallback_to_secondary_when_primary_low() -> None:
    primary = Mock()
    secondary = Mock()

    primary_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="LOW",
        quality_reason="Not enough relevant articles",
        articles_after_filter=0,
    )

    secondary_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[
            NewsArticle(
                title="EUR USD Exchange Rate Rises",
                relevance_score=0.6,
                query_tag="pair",
            ),
            NewsArticle(
                title="ECB Announces Policy",
                relevance_score=0.6,
                query_tag="macro",
            ),
        ],
        quality="MEDIUM",
        quality_reason="Found 2 highly relevant articles",
        articles_after_filter=2,
    )

    primary.get_news_digest.return_value = primary_digest
    secondary.get_news_digest.return_value = secondary_digest

    multi_provider = MultiNewsProvider(primary=primary, secondary=secondary)

    result = multi_provider.get_news_digest("EURUSD", Timeframe.H1)

    assert result.provider_used == "NEWSAPI"
    assert result.quality == "MEDIUM"
    assert result.primary_quality == "LOW"
    assert result.primary_reason == "Not enough relevant articles"
    assert result.secondary_quality == "MEDIUM"
    assert result.secondary_reason == "Found 2 highly relevant articles"
    primary.get_news_digest.assert_called_once()
    secondary.get_news_digest.assert_called_once()


def test_multi_provider_returns_none_when_both_low() -> None:
    primary = Mock()
    secondary = Mock()

    primary_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="LOW",
        quality_reason="Not enough relevant articles from GDELT",
        articles_after_filter=0,
    )

    secondary_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="LOW",
        quality_reason="Not enough relevant articles from NewsAPI",
        articles_after_filter=0,
    )

    primary.get_news_digest.return_value = primary_digest
    secondary.get_news_digest.return_value = secondary_digest

    multi_provider = MultiNewsProvider(primary=primary, secondary=secondary)

    result = multi_provider.get_news_digest("EURUSD", Timeframe.H1)

    assert result.provider_used == "NONE"
    assert result.quality == "LOW"
    assert "GDELT LOW" in result.quality_reason
    assert "NewsAPI LOW" in result.quality_reason
    assert result.primary_quality == "LOW"
    assert result.secondary_quality == "LOW"
    primary.get_news_digest.assert_called_once()
    secondary.get_news_digest.assert_called_once()


def test_multi_provider_no_secondary_provider() -> None:
    primary = Mock()

    primary_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[],
        quality="LOW",
        quality_reason="Not enough relevant articles",
        articles_after_filter=0,
    )

    primary.get_news_digest.return_value = primary_digest

    multi_provider = MultiNewsProvider(primary=primary, secondary=None)

    result = multi_provider.get_news_digest("EURUSD", Timeframe.H1)

    assert result.provider_used == "GDELT"
    assert result.quality == "LOW"
    assert "NewsAPI disabled" in result.quality_reason
    assert result.primary_quality == "LOW"
    primary.get_news_digest.assert_called_once()


def test_multi_provider_primary_low_but_articles_after_filter_less_than_2() -> None:
    primary = Mock()
    secondary = Mock()

    primary_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[
            NewsArticle(
                title="EUR USD Exchange Rate Rises",
                relevance_score=0.6,
                query_tag="pair",
            ),
        ],
        quality="MEDIUM",
        quality_reason="Found 1 article",
        articles_after_filter=1,
    )

    secondary_digest = NewsDigest(
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        window_hours=24,
        articles=[
            NewsArticle(
                title="ECB Announces Policy",
                relevance_score=0.6,
                query_tag="macro",
            ),
            NewsArticle(
                title="Fed Rate Decision",
                relevance_score=0.6,
                query_tag="macro",
            ),
        ],
        quality="MEDIUM",
        quality_reason="Found 2 highly relevant articles",
        articles_after_filter=2,
    )

    primary.get_news_digest.return_value = primary_digest
    secondary.get_news_digest.return_value = secondary_digest

    multi_provider = MultiNewsProvider(primary=primary, secondary=secondary)

    result = multi_provider.get_news_digest("EURUSD", Timeframe.H1)

    assert result.provider_used == "NEWSAPI"
    assert result.quality == "MEDIUM"
    primary.get_news_digest.assert_called_once()
    secondary.get_news_digest.assert_called_once()
