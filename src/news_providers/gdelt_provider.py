import re
import string
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

import httpx

from src.core.models.news import NewsArticle, NewsDigest
from src.core.models.timeframe import Timeframe
from src.core.ports.news_provider import NewsProvider


class GDELTProvider(NewsProvider):
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def _build_query_from_symbol(self, symbol: str) -> str:
        symbol_upper = symbol.upper().strip()
        if len(symbol_upper) == 6:
            return f"{symbol_upper[:3]} {symbol_upper[3:]}"
        return symbol_upper.replace("_", " ")

    def _get_query_templates(self, symbol: str) -> dict[str, str]:
        symbol_upper = symbol.upper().strip()
        base_currencies = symbol_upper[:3] if len(symbol_upper) >= 3 else ""
        quote_currency = symbol_upper[3:6] if len(symbol_upper) >= 6 else ""

        currency_names: dict[str, dict[str, str]] = {
            "EUR": {"name": "euro", "cb": "ECB"},
            "USD": {"name": "dollar", "cb": "Fed"},
            "GBP": {"name": "pound", "cb": "BoE"},
            "JPY": {"name": "yen", "cb": "BoJ"},
            "AUD": {"name": "australian dollar", "cb": "RBA"},
            "CAD": {"name": "canadian dollar", "cb": "BoC"},
            "CHF": {"name": "swiss franc", "cb": "SNB"},
            "NZD": {"name": "new zealand dollar", "cb": "RBNZ"},
        }

        base_info = currency_names.get(base_currencies, {"name": base_currencies.lower(), "cb": ""})
        quote_info = currency_names.get(quote_currency, {"name": quote_currency.lower(), "cb": ""})

        pair_query_parts: list[str] = []
        if base_currencies and quote_currency:
            pair_query_parts.append(f"{base_currencies} {quote_currency}")
            pair_query_parts.append(f"{base_info['name']} {quote_info['name']}")
            pair_query_parts.append("forex OR fx OR currency")
        pair_query = " AND ".join(pair_query_parts) if pair_query_parts else f"{symbol_upper} forex"

        macro_query_parts: list[str] = []
        if base_currencies or quote_currency:
            currencies = [c for c in [base_currencies, quote_currency] if c]
            macro_query_parts.append(" OR ".join(currencies))
            macro_query_parts.append("(CPI OR inflation OR rates OR yields OR NFP OR GDP OR PMI)")
            macro_query_parts.append("(forex OR fx OR currency)")
        macro_query = " AND ".join(macro_query_parts) if macro_query_parts else f"{symbol_upper} macro"

        risk_query_parts: list[str] = []
        if base_currencies or quote_currency:
            currencies = [c for c in [base_currencies, quote_currency] if c]
            risk_query_parts.append(" OR ".join(currencies))
            cb_names = [info["cb"] for info in [base_info, quote_info] if info["cb"]]
            if cb_names:
                risk_query_parts.append(f"({' OR '.join(cb_names)})")
            risk_query_parts.append("(forex OR fx OR currency OR risk OR volatility)")
        risk_query = " AND ".join(risk_query_parts) if risk_query_parts else f"{symbol_upper} risk"

        language_filter = "sourcelang:English"

        return {
            "pair": f"({pair_query}) {language_filter}",
            "macro": f"({macro_query}) {language_filter}",
            "risk": f"({risk_query}) {language_filter}",
        }

    def fetch_articles(self, symbol: str) -> list[NewsArticle]:
        templates = self._get_query_templates(symbol)
        all_candidates: list[NewsArticle] = []

        for query_tag, query in templates.items():
            try:
                url = f"{self.base_url}/api/v2/doc/doc"
                params: dict[str, str | int] = {
                    "query": query,
                    "mode": "artlist",
                    "format": "json",
                    "maxrecords": 15,
                    "timespan": "24h",
                    "sort": "datedesc",
                }

                response = self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                articles_data = data.get("articles", [])

                for article_data in articles_data:
                    title = article_data.get("title", "").strip()
                    if not title:
                        continue

                    url_str = article_data.get("url", "").strip() or None
                    source = article_data.get("source", "").strip() or None
                    language = article_data.get("language", "").strip() or None

                    published_at: Optional[datetime] = None
                    seendate_str = article_data.get("seendate")
                    if seendate_str:
                        try:
                            seendate_int = int(seendate_str)
                            year = seendate_int // 10000
                            month = (seendate_int // 100) % 100
                            day = seendate_int % 100
                            hour = (seendate_int // 1000000) % 100 if seendate_int >= 1000000 else 0
                            minute = (seendate_int // 10000) % 100 if seendate_int >= 1000000 else 0
                            published_at = datetime(year, month, day, hour, minute)
                        except (ValueError, TypeError):
                            pass

                    all_candidates.append(
                        NewsArticle(
                            title=title,
                            url=url_str,
                            source=source,
                            published_at=published_at,
                            language=language,
                            relevance_score=0.0,
                            query_tag=query_tag,
                        )
                    )
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError, KeyError, ValueError, TypeError):
                continue

        filtered_articles, _, _ = self._filter_dedup_score(all_candidates, symbol)
        return filtered_articles

    def _normalize_title(self, title: str) -> str:
        title_lower = title.lower()
        title_no_punct = "".join(c if c.isalnum() or c.isspace() else " " for c in title_lower)
        title_normalized = " ".join(title_no_punct.split())
        return title_normalized

    def _filter_dedup_score(
        self, articles: list[NewsArticle], symbol: str
    ) -> tuple[list[NewsArticle], list[str], Optional[str]]:
        symbol_upper = symbol.upper().strip()
        base_currency = symbol_upper[:3] if len(symbol_upper) >= 3 else ""
        quote_currency = symbol_upper[3:6] if len(symbol_upper) >= 6 else ""

        currency_names: dict[str, dict[str, list[str]]] = {
            "EUR": {"names": ["euro", "eur"], "cb": ["ecb", "european central bank"]},
            "USD": {"names": ["dollar", "usd", "dollar"], "cb": ["fed", "federal reserve"]},
            "GBP": {"names": ["pound", "gbp", "sterling"], "cb": ["boe", "bank of england"]},
            "JPY": {"names": ["yen", "jpy"], "cb": ["boj", "bank of japan"]},
            "AUD": {"names": ["australian dollar", "aud"], "cb": ["rba", "reserve bank of australia"]},
            "CAD": {"names": ["canadian dollar", "cad"], "cb": ["boc", "bank of canada"]},
            "CHF": {"names": ["swiss franc", "chf"], "cb": ["snb", "swiss national bank"]},
            "NZD": {"names": ["new zealand dollar", "nzd"], "cb": ["rbnz", "reserve bank of new zealand"]},
        }

        base_info = currency_names.get(base_currency, {"names": [base_currency.lower()], "cb": []})
        quote_info = currency_names.get(quote_currency, {"names": [quote_currency.lower()], "cb": []})

        fx_anchors = ["forex", "fx", "currency", "exchange rate", "foreign exchange"]
        macro_keywords = ["cpi", "inflation", "rates", "yields", "jobs", "nfp", "gdp", "pmi", "employment", "unemployment"]
        blacklist_phrases = [
            "exchange rates today",
            "курс валют сегодня",
            "currency converter",
            "live rates",
            "today's rates",
            "current exchange rate",
        ]

        now = datetime.now()
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
                has_currency_mention = has_currency_mention or any(name in title_lower for name in quote_info["names"])

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
                age_hours = (now - article.published_at).total_seconds() / 3600.0
                if age_hours < 4.0:
                    score += 0.1

            score = min(1.0, max(0.0, score))

            article.relevance_score = score
            deduplicated.append(article)

        filtered_sorted = sorted(deduplicated, key=lambda a: a.relevance_score, reverse=True)

        dropped_reason_hint: Optional[str] = None
        if drop_reasons:
            most_common = Counter(drop_reasons).most_common(1)[0][0]
            dropped_reason_hint = most_common

        return filtered_sorted, dropped_examples, dropped_reason_hint

    def get_news_digest(self, symbol: str, timeframe: Timeframe) -> NewsDigest:
        try:
            templates = self._get_query_templates(symbol)
            all_candidates: list[NewsArticle] = []

            for query_tag, query in templates.items():
                try:
                    url = f"{self.base_url}/api/v2/doc/doc"
                    params: dict[str, str | int] = {
                        "query": query,
                        "mode": "artlist",
                        "format": "json",
                        "maxrecords": 15,
                        "timespan": "24h",
                        "sort": "datedesc",
                    }

                    response = self.client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    articles_data = data.get("articles", [])

                    for article_data in articles_data:
                        title = article_data.get("title", "").strip()
                        if not title:
                            continue

                        url_str = article_data.get("url", "").strip() or None
                        source = article_data.get("source", "").strip() or None
                        language = article_data.get("language", "").strip() or None

                        published_at: Optional[datetime] = None
                        seendate_str = article_data.get("seendate")
                        if seendate_str:
                            try:
                                seendate_int = int(seendate_str)
                                year = seendate_int // 10000
                                month = (seendate_int // 100) % 100
                                day = seendate_int % 100
                                hour = (seendate_int // 1000000) % 100 if seendate_int >= 1000000 else 0
                                minute = (seendate_int // 10000) % 100 if seendate_int >= 1000000 else 0
                                published_at = datetime(year, month, day, hour, minute)
                            except (ValueError, TypeError):
                                pass

                        all_candidates.append(
                            NewsArticle(
                                title=title,
                                url=url_str,
                                source=source,
                                published_at=published_at,
                                language=language,
                                relevance_score=0.0,
                                query_tag=query_tag,
                            )
                        )
                except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError, KeyError, ValueError, TypeError):
                    continue

            candidates_total = len(all_candidates)
            filtered_articles, dropped_examples, dropped_reason_hint = self._filter_dedup_score(all_candidates, symbol)
            articles_after_filter = len(filtered_articles)
            top_articles = filtered_articles[:10]

            high_score_count = sum(1 for a in top_articles if a.relevance_score >= 0.55)

            if high_score_count >= 5:
                quality = "HIGH"
                quality_reason = f"Found {high_score_count} highly relevant articles (score >= 0.55)"
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
                dropped_examples=dropped_examples if quality == "LOW" else [],
                dropped_reason_hint=dropped_reason_hint if quality == "LOW" else None,
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
            )

    def get_news_summary(self, symbol: str) -> str:
        try:
            digest = self.get_news_digest(symbol, Timeframe.H1)
            if digest.summary:
                return digest.summary
            return "No news found via GDELT."
        except Exception:
            return "No news found via GDELT."

    def __del__(self) -> None:
        if hasattr(self, "client"):
            self.client.close()
