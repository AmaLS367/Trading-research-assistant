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

    def _get_query_templates(self, symbol: str) -> dict[str, dict[str, str]]:
        symbol_upper = symbol.upper().strip()
        base_currencies = symbol_upper[:3] if len(symbol_upper) >= 3 else ""
        quote_currency = symbol_upper[3:6] if len(symbol_upper) >= 6 else ""

        currency_names: dict[str, dict[str, str]] = {
            "EUR": {"name": "euro", "cb": "ECB", "cb_full": "European Central Bank"},
            "USD": {"name": "dollar", "cb": "Fed", "cb_full": "Federal Reserve"},
            "GBP": {"name": "pound", "cb": "BoE", "cb_full": "Bank of England"},
            "JPY": {"name": "yen", "cb": "BoJ", "cb_full": "Bank of Japan"},
            "AUD": {"name": "australian dollar", "cb": "RBA", "cb_full": "Reserve Bank of Australia"},
            "CAD": {"name": "canadian dollar", "cb": "BoC", "cb_full": "Bank of Canada"},
            "CHF": {"name": "swiss franc", "cb": "SNB", "cb_full": "Swiss National Bank"},
            "NZD": {"name": "new zealand dollar", "cb": "RBNZ", "cb_full": "Reserve Bank of New Zealand"},
        }

        base_info = currency_names.get(base_currencies, {"name": base_currencies.lower(), "cb": "", "cb_full": ""})
        quote_info = currency_names.get(quote_currency, {"name": quote_currency.lower(), "cb": "", "cb_full": ""})

        fx_anchors = '(forex OR fx OR currency OR "exchange rate" OR "foreign exchange")'
        language_filter = "sourcelang:English"

        templates: dict[str, dict[str, str]] = {
            "strict": {},
            "medium": {},
            "broad": {},
        }

        if base_currencies and quote_currency:
            pair_ticker = f"{base_currencies}{quote_currency}"
            pair_slash = f"{base_currencies}/{quote_currency}"
            base_name = base_info["name"]
            quote_name = quote_info["name"]

            templates["strict"]["pair_strict"] = (
                f'(({pair_ticker} OR "{pair_slash}" OR ("{base_name}" AND "{quote_name}")) AND {fx_anchors}) {language_filter}'
            )

            templates["medium"]["pair_medium"] = (
                f'(("{base_name}" AND "{quote_name}") AND {fx_anchors}) {language_filter}'
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

        macro_terms = '(CPI OR inflation OR "interest rate" OR rates OR yields OR NFP OR GDP OR PMI OR employment OR unemployment)'

        if cb_terms:
            cb_query = " OR ".join(cb_terms)
            templates["medium"]["macro_medium"] = (
                f'(({cb_query} OR {macro_terms}) AND {fx_anchors}) {language_filter}'
            )

        templates["broad"]["macro_broad"] = (
            f'({macro_terms} AND {fx_anchors}) {language_filter}'
        )

        risk_terms = '("risk on" OR "risk off" OR recession OR "safe haven" OR "market volatility" OR volatility)'
        templates["broad"]["risk_broad"] = (
            f'({risk_terms} AND {fx_anchors}) {language_filter}'
        )

        return templates

    def _fetch_articles_for_query(self, query: str, query_tag: str) -> tuple[list[NewsArticle], dict]:
        articles: list[NewsArticle] = []
        debug_info: dict = {
            "tag": query_tag,
            "query": query[:200] if len(query) > 200 else query,
            "url": "",
            "http_status": None,
            "error": None,
            "json_keys": None,
            "items_count": 0,
            "sample_title": None,
            "json_parse_error": None,
        }

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

            from urllib.parse import urlencode
            query_string = urlencode(params)
            full_url = f"{url}?{query_string}"
            debug_info["url"] = full_url

            response = self.client.get(url, params=params)
            debug_info["http_status"] = response.status_code
            response.raise_for_status()

            try:
                data = response.json()
                debug_info["json_keys"] = list(data.keys())[:10] if isinstance(data, dict) else None
                articles_data = data.get("articles", [])
                debug_info["items_count"] = len(articles_data) if isinstance(articles_data, list) else 0

                if articles_data and isinstance(articles_data, list) and len(articles_data) > 0:
                    first_item = articles_data[0]
                    if isinstance(first_item, dict):
                        sample_title = first_item.get("title", "")
                        if sample_title:
                            debug_info["sample_title"] = str(sample_title)[:100]

                for article_data in articles_data:
                    if not isinstance(article_data, dict):
                        continue
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

                    articles.append(
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
            except (ValueError, TypeError, KeyError) as json_error:
                debug_info["json_parse_error"] = str(json_error)[:200]
        except httpx.HTTPStatusError as http_error:
            debug_info["http_status"] = http_error.response.status_code if http_error.response else None
            debug_info["error"] = f"HTTP {http_error.response.status_code if http_error.response else 'unknown'}: {str(http_error)[:200]}"
        except (httpx.TimeoutException, httpx.NetworkError) as network_error:
            debug_info["error"] = f"{type(network_error).__name__}: {str(network_error)[:200]}"
        except Exception as e:
            debug_info["error"] = f"{type(e).__name__}: {str(e)[:200]}"

        return articles, debug_info

    def fetch_articles_with_fallback(
        self, symbol: str
    ) -> tuple[list[NewsArticle], dict[str, dict[str, int]], dict[str, str], dict]:
        templates = self._get_query_templates(symbol)
        all_candidates: list[NewsArticle] = []
        pass_counts: dict[str, dict[str, int]] = {}
        queries_used: dict[str, str] = {}
        gdelt_debug: dict = {"passes": {}}

        passes = ["strict", "medium", "broad"]
        threshold = 0.55
        min_relevant = 2

        for pass_name in passes:
            if pass_name not in templates or not templates[pass_name]:
                continue

            pass_candidates: list[NewsArticle] = []
            pass_requests: list[dict] = []

            for query_tag, query in templates[pass_name].items():
                articles, debug_info = self._fetch_articles_for_query(query, query_tag)
                pass_candidates.extend(articles)
                queries_used[query_tag] = query[:100] if len(query) > 100 else query
                pass_requests.append(debug_info)

            all_candidates.extend(pass_candidates)
            gdelt_debug["passes"][pass_name] = {"requests": pass_requests}

            filtered_articles, _, _ = self._filter_dedup_score(all_candidates, symbol)

            relevant_high = [a for a in filtered_articles if a.relevance_score >= threshold]

            if pass_name == "broad" and len(relevant_high) < min_relevant:
                filtered_articles_broad = [
                    a for a in filtered_articles
                    if a.relevance_score >= 0.45
                    and any(anchor in a.title.lower() for anchor in ["forex", "fx", "currency", "exchange rate", "foreign exchange"])
                ]
                if filtered_articles_broad:
                    filtered_articles = filtered_articles_broad
                    relevant_count = len(filtered_articles)
                else:
                    filtered_articles = relevant_high
                    relevant_count = len(filtered_articles)
            else:
                filtered_articles = relevant_high
                relevant_count = len(filtered_articles)

            pass_counts[pass_name] = {
                "candidates": len(pass_candidates),
                "after_filter": len(filtered_articles),
            }

            if relevant_count >= min_relevant:
                return filtered_articles, pass_counts, queries_used, gdelt_debug

        final_filtered, _, _ = self._filter_dedup_score(all_candidates, symbol)
        final_filtered = [a for a in final_filtered if a.relevance_score >= threshold]

        if len(final_filtered) < min_relevant and "broad" in pass_counts:
            final_filtered_broad = [
                a for a in final_filtered
                if a.relevance_score >= 0.45
                and any(anchor in a.title.lower() for anchor in ["forex", "fx", "currency", "exchange rate", "foreign exchange"])
            ]
            if final_filtered_broad:
                final_filtered = final_filtered_broad

        return final_filtered, pass_counts, queries_used, gdelt_debug

    def fetch_articles(self, symbol: str) -> list[NewsArticle]:
        articles, _, _, _ = self.fetch_articles_with_fallback(symbol)
        return articles

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
            filtered_articles, pass_counts, queries_used, gdelt_debug = self.fetch_articles_with_fallback(symbol)

            candidates_total = sum(counts.get("candidates", 0) for counts in pass_counts.values())
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

            dropped_examples: list[str] = []
            dropped_reason_hint: Optional[str] = None
            if quality == "LOW":
                all_candidates_for_dropped: list[NewsArticle] = []
                templates = self._get_query_templates(symbol)
                for pass_name in ["strict", "medium", "broad"]:
                    if pass_name in templates:
                        for query_tag, query in templates[pass_name].items():
                            articles, _ = self._fetch_articles_for_query(query, query_tag)
                            all_candidates_for_dropped.extend(articles)
                _, dropped_examples, dropped_reason_hint = self._filter_dedup_score(all_candidates_for_dropped, symbol)
                dropped_examples = dropped_examples[:3]

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
                dropped_examples=dropped_examples,
                dropped_reason_hint=dropped_reason_hint,
                pass_counts=pass_counts,
                queries_used=queries_used,
                gdelt_debug=gdelt_debug,
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
                gdelt_debug={},
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
