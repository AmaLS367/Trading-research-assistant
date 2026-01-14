from collections import Counter
from datetime import UTC, datetime

import httpx

from src.core.models.news import NewsArticle, NewsDigest
from src.core.models.timeframe import Timeframe
from src.core.ports.news_provider import NewsProvider


class NewsAPIProvider(NewsProvider):
    def __init__(self, api_key: str, base_url: str, timeout: float = 10.0) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def _get_query_templates(self, symbol: str) -> dict[str, str]:
        symbol_upper = symbol.upper().strip()
        base_currency = symbol_upper[:3] if len(symbol_upper) >= 3 else ""
        quote_currency = symbol_upper[3:6] if len(symbol_upper) >= 6 else ""

        currency_names: dict[str, dict[str, str]] = {
            "EUR": {"name": "euro", "cb": "ECB", "cb_full": "European Central Bank"},
            "USD": {"name": "dollar", "cb": "Fed", "cb_full": "Federal Reserve"},
            "GBP": {"name": "pound", "cb": "BoE", "cb_full": "Bank of England"},
            "JPY": {"name": "yen", "cb": "BoJ", "cb_full": "Bank of Japan"},
            "AUD": {
                "name": "australian dollar",
                "cb": "RBA",
                "cb_full": "Reserve Bank of Australia",
            },
            "CAD": {"name": "canadian dollar", "cb": "BoC", "cb_full": "Bank of Canada"},
            "CHF": {"name": "swiss franc", "cb": "SNB", "cb_full": "Swiss National Bank"},
            "NZD": {
                "name": "new zealand dollar",
                "cb": "RBNZ",
                "cb_full": "Reserve Bank of New Zealand",
            },
        }

        base_info = currency_names.get(
            base_currency, {"name": base_currency.lower(), "cb": "", "cb_full": ""}
        )
        quote_info = currency_names.get(
            quote_currency, {"name": quote_currency.lower(), "cb": "", "cb_full": ""}
        )

        fx_anchors = 'forex OR fx OR currency OR "exchange rate"'
        templates: dict[str, str] = {}

        if base_currency and quote_currency:
            pair_ticker = f"{base_currency}{quote_currency}"
            pair_slash = f"{base_currency}/{quote_currency}"
            base_name = base_info["name"]
            quote_name = quote_info["name"]

            templates["pair"] = (
                f'({pair_ticker} OR "{pair_slash}" OR ({base_name} AND {quote_name})) AND ({fx_anchors})'
            )

        cb_terms: list[str] = []
        if base_info["cb"]:
            cb_terms.append(base_info["cb"])
        if base_info["cb_full"]:
            cb_terms.append(f'"{base_info["cb_full"]}"')
        if quote_info["cb"]:
            cb_terms.append(quote_info["cb"])
        if quote_info["cb_full"]:
            cb_terms.append(f'"{quote_info["cb_full"]}"')

        macro_terms = 'CPI OR inflation OR "interest rate" OR rates OR yields OR NFP OR GDP OR PMI'

        if cb_terms:
            cb_query = " OR ".join(cb_terms)
            templates["macro"] = f"({cb_query} OR {macro_terms}) AND ({fx_anchors})"

        return templates

    def _fetch_articles_for_query(self, query: str, query_tag: str) -> list[NewsArticle]:
        articles: list[NewsArticle] = []
        try:
            url = f"{self.base_url}/v2/everything"
            params: dict[str, str | int] = {
                "q": query,
                "language": "en",
                "pageSize": 20,
                "sortBy": "publishedAt",
                "apiKey": self.api_key,
            }

            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            articles_data = data.get("articles", [])

            for article_data in articles_data:
                if not isinstance(article_data, dict):
                    continue
                title = article_data.get("title", "").strip()
                if not title:
                    continue

                url_str = article_data.get("url", "").strip() or None
                source_obj = article_data.get("source", {})
                source = (
                    source_obj.get("name", "").strip() if isinstance(source_obj, dict) else None
                )

                published_at: datetime | None = None
                published_str = article_data.get("publishedAt")
                if published_str:
                    try:
                        if isinstance(published_str, str):
                            published_at = datetime.fromisoformat(
                                published_str.replace("Z", "+00:00")
                            )
                    except (ValueError, TypeError, AttributeError):
                        pass

                articles.append(
                    NewsArticle(
                        title=title,
                        url=url_str,
                        source=source,
                        published_at=published_at,
                        language="en",
                        relevance_score=0.0,
                        query_tag=query_tag,
                    )
                )
        except (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.HTTPStatusError,
            KeyError,
            ValueError,
            TypeError,
        ):
            pass

        return articles

    def _normalize_title(self, title: str) -> str:
        title_lower = title.lower()
        title_no_punct = "".join(c if c.isalnum() or c.isspace() else " " for c in title_lower)
        title_normalized = " ".join(title_no_punct.split())
        return title_normalized

    def _filter_dedup_score(
        self, articles: list[NewsArticle], symbol: str
    ) -> tuple[list[NewsArticle], list[str], str | None]:
        symbol_upper = symbol.upper().strip()
        base_currency = symbol_upper[:3] if len(symbol_upper) >= 3 else ""
        quote_currency = symbol_upper[3:6] if len(symbol_upper) >= 6 else ""

        currency_names: dict[str, dict[str, list[str]]] = {
            "EUR": {"names": ["euro", "eur"], "cb": ["ecb", "european central bank"]},
            "USD": {"names": ["dollar", "usd", "dollar"], "cb": ["fed", "federal reserve"]},
            "GBP": {"names": ["pound", "gbp", "sterling"], "cb": ["boe", "bank of england"]},
            "JPY": {"names": ["yen", "jpy"], "cb": ["boj", "bank of japan"]},
            "AUD": {
                "names": ["australian dollar", "aud"],
                "cb": ["rba", "reserve bank of australia"],
            },
            "CAD": {"names": ["canadian dollar", "cad"], "cb": ["boc", "bank of canada"]},
            "CHF": {"names": ["swiss franc", "chf"], "cb": ["snb", "swiss national bank"]},
            "NZD": {
                "names": ["new zealand dollar", "nzd"],
                "cb": ["rbnz", "reserve bank of new zealand"],
            },
        }

        base_info = currency_names.get(base_currency, {"names": [base_currency.lower()], "cb": []})
        quote_info = currency_names.get(
            quote_currency, {"names": [quote_currency.lower()], "cb": []}
        )

        fx_anchors = ["forex", "fx", "currency", "exchange rate", "foreign exchange"]
        macro_keywords = [
            "cpi",
            "inflation",
            "rates",
            "yields",
            "jobs",
            "nfp",
            "gdp",
            "pmi",
            "employment",
            "unemployment",
        ]
        blacklist_phrases = [
            "exchange rates today",
            "курс валют сегодня",
            "currency converter",
            "live rates",
            "today's rates",
            "current exchange rate",
        ]

        now = datetime.now(UTC)
        deduplicated: list[NewsArticle] = []
        seen_normalized: set[str] = set()
        dropped_examples: list[str] = []
        drop_reasons: list[str] = []

        for article in articles:
            title = article.title.strip()
            if len(title) < 10:
                if len(dropped_examples) < 3:
                    dropped_examples.append(title[:80] if len(title) > 80 else title)
                drop_reasons.append("too_short")
                continue

            title_lower = title.lower()
            is_blacklisted = any(phrase in title_lower for phrase in blacklist_phrases)
            if is_blacklisted:
                if len(dropped_examples) < 3:
                    dropped_examples.append(title[:80] if len(title) > 80 else title)
                drop_reasons.append("blacklisted")
                continue

            normalized = self._normalize_title(title)
            if normalized in seen_normalized:
                if len(dropped_examples) < 3:
                    dropped_examples.append(title[:80] if len(title) > 80 else title)
                drop_reasons.append("dedup")
                continue
            if len(normalized) < 10:
                if len(dropped_examples) < 3:
                    dropped_examples.append(title[:80] if len(title) > 80 else title)
                drop_reasons.append("too_short")
                continue

            seen_normalized.add(normalized)

            has_fx_anchor = any(anchor in title_lower for anchor in fx_anchors)
            has_currency_mention = False
            if base_currency:
                has_currency_mention = any(name in title_lower for name in base_info["names"])
            if quote_currency:
                has_currency_mention = has_currency_mention or any(
                    name in title_lower for name in quote_info["names"]
                )

            has_cb_mention = False
            if base_info["cb"]:
                has_cb_mention = any(cb in title_lower for cb in base_info["cb"])
            if quote_info["cb"]:
                has_cb_mention = has_cb_mention or any(cb in title_lower for cb in quote_info["cb"])

            has_macro = any(keyword in title_lower for keyword in macro_keywords)

            if not (has_fx_anchor or has_currency_mention or has_cb_mention or has_macro):
                if len(dropped_examples) < 3:
                    dropped_examples.append(title[:80] if len(title) > 80 else title)
                drop_reasons.append("no_fx_anchors")
                continue

            score = 0.0

            if base_currency and quote_currency:
                base_in_title = any(name in title_lower for name in base_info["names"])
                quote_in_title = any(name in title_lower for name in quote_info["names"])
                if base_in_title and quote_in_title:
                    score += 0.3
                elif base_in_title or quote_in_title:
                    score += 0.15

            if has_cb_mention:
                score += 0.2

            if has_macro:
                score += 0.2

            if article.published_at:
                if article.published_at.tzinfo is None:
                    published_at_aware = article.published_at.replace(tzinfo=UTC)
                else:
                    published_at_aware = article.published_at
                age_hours = (now - published_at_aware).total_seconds() / 3600.0
                if age_hours < 4.0:
                    score += 0.1

            score = min(1.0, max(0.0, score))

            article.relevance_score = score
            deduplicated.append(article)

        filtered_sorted = sorted(deduplicated, key=lambda a: a.relevance_score, reverse=True)

        dropped_reason_hint: str | None = None
        if drop_reasons:
            most_common = Counter(drop_reasons).most_common(1)[0][0]
            dropped_reason_hint = most_common

        return filtered_sorted, dropped_examples, dropped_reason_hint

    def get_news_digest(self, symbol: str, timeframe: Timeframe) -> NewsDigest:
        try:
            templates = self._get_query_templates(symbol)
            all_candidates: list[NewsArticle] = []

            for query_tag, query in templates.items():
                articles = self._fetch_articles_for_query(query, query_tag)
                all_candidates.extend(articles)

            filtered_articles, dropped_examples, dropped_reason_hint = self._filter_dedup_score(
                all_candidates, symbol
            )

            candidates_total = len(all_candidates)
            articles_after_filter = len(filtered_articles)
            top_articles = filtered_articles[:10]

            high_score_count = sum(1 for a in top_articles if a.relevance_score >= 0.55)

            if high_score_count >= 5:
                quality = "HIGH"
                quality_reason = (
                    f"Found {high_score_count} highly relevant articles (score >= 0.55)"
                )
            elif high_score_count >= 2 or len(top_articles) >= 2:
                quality = "MEDIUM"
                quality_reason = f"Found {high_score_count} highly relevant articles, {len(top_articles)} total after filtering"
            else:
                quality = "LOW"
                quality_reason = "Not enough relevant articles after filtering"

            summary_parts: list[str] = [f"Quality {quality}."]
            if top_articles:
                summary_parts.append("Top headlines:")
                for article in top_articles[:5]:
                    summary_parts.append(f"- {article.title}")
            summary = " ".join(summary_parts)

            if quality == "LOW" and not dropped_examples:
                dropped_examples = [a.title[:80] for a in all_candidates[:3] if a.title]

            return NewsDigest(
                symbol=symbol,
                timeframe=timeframe,
                window_hours=24,
                articles=top_articles,
                quality=quality,
                quality_reason=quality_reason,
                summary=summary,
                sentiment=None,
                impact_score=None,
                candidates_total=candidates_total,
                articles_after_filter=articles_after_filter,
                dropped_examples=dropped_examples[:3],
                dropped_reason_hint=dropped_reason_hint,
                pass_counts={},
                queries_used={},
            )
        except Exception as e:
            return NewsDigest(
                symbol=symbol,
                timeframe=timeframe,
                window_hours=24,
                articles=[],
                quality="LOW",
                quality_reason=f"Error fetching or processing news: {type(e).__name__}",
                summary="Quality LOW. Error fetching news.",
                sentiment=None,
                impact_score=None,
                candidates_total=0,
                articles_after_filter=0,
                dropped_examples=[],
                dropped_reason_hint=None,
                pass_counts={},
                queries_used={},
            )

    def get_news_summary(self, symbol: str) -> str:
        try:
            digest = self.get_news_digest(symbol, Timeframe.H1)
            if digest.summary:
                return digest.summary
            return "No news found via NewsAPI."
        except Exception:
            return "No news found via NewsAPI."

    def __del__(self) -> None:
        if hasattr(self, "client"):
            self.client.close()
