import json
import logging
import os
from datetime import datetime
from typing import TYPE_CHECKING, Any

from src.agents.news_analyst import NewsAnalyst
from src.agents.synthesizer import Synthesizer
from src.agents.technical_analyst import TechnicalAnalyst
from src.core.models.rationale import Rationale, RationaleType
from src.core.models.run import Run, RunStatus
from src.core.models.timeframe import Timeframe
from src.core.ports.market_data_provider import MarketDataProvider
from src.core.ports.news_provider import NewsProvider
from src.features.indicators.indicator_engine import calculate_features
from src.features.snapshots.feature_snapshot import FeatureSnapshot
from src.storage.sqlite.repositories.rationales_repository import RationalesRepository
from src.storage.sqlite.repositories.recommendations_repository import RecommendationsRepository
from src.storage.sqlite.repositories.runs_repository import RunsRepository

if TYPE_CHECKING:
    from rich.console import Console


logger = logging.getLogger(__name__)


def _trim_text(value: object, max_len: int) -> str | None:
    if value is None:
        return None
    text = str(value)
    if len(text) <= max_len:
        return text
    return text[:max_len]


def _is_news_debug_enabled() -> bool:
    value = os.getenv("TRA_NEWS_DEBUG", "").strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


def _truncate_single_line(text: str, max_len: int) -> str:
    cleaned = " ".join(text.strip().split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[:max_len].rstrip() + " ... [truncated]"


def _sanitize_gdelt_debug(
    gdelt_debug: object,
    *,
    max_requests_per_pass: int = 3,
    max_body_preview_len: int = 200,
    max_query_len: int = 200,
) -> dict[str, object] | None:
    if not isinstance(gdelt_debug, dict):
        return None

    passes = gdelt_debug.get("passes")
    if not isinstance(passes, dict):
        return None

    sanitized: dict[str, object] = {}
    sanitized_passes: dict[str, object] = {}

    for pass_name, pass_data in passes.items():
        if not isinstance(pass_data, dict):
            continue

        requests = pass_data.get("requests", [])
        sanitized_pass_data: dict[str, object] = {}

        if isinstance(requests, list):
            sanitized_requests: list[dict[str, object]] = []
            for req in requests[:max_requests_per_pass]:
                if not isinstance(req, dict):
                    continue
                req_copy: dict[str, object] = dict(req)
                if "body_preview" in req_copy:
                    req_copy["body_preview"] = _trim_text(
                        req_copy.get("body_preview"), max_body_preview_len
                    )
                if "query" in req_copy:
                    req_copy["query"] = _trim_text(req_copy.get("query"), max_query_len)
                if "url" in req_copy:
                    req_copy["url"] = _trim_text(req_copy.get("url"), max_query_len)
                if "json_parse_error" in req_copy:
                    req_copy["json_parse_error"] = _trim_text(req_copy.get("json_parse_error"), 200)
                if "error" in req_copy:
                    req_copy["error"] = _trim_text(req_copy.get("error"), 200)
                if "content_type" in req_copy:
                    req_copy["content_type"] = _trim_text(req_copy.get("content_type"), 80)
                sanitized_requests.append(req_copy)
            sanitized_pass_data["requests"] = sanitized_requests

        sanitized_passes[str(pass_name)] = sanitized_pass_data

    sanitized["passes"] = sanitized_passes
    return sanitized


def _sanitize_queries_used(queries_used: object, *, max_items: int = 10) -> dict[str, str] | None:
    if not isinstance(queries_used, dict):
        return None

    sanitized: dict[str, str] = {}
    for key, value in list(queries_used.items())[:max_items]:
        sanitized[str(key)] = _trim_text(value, 200) or ""
    return sanitized


class RunAgentsJob:
    def __init__(
        self,
        market_data_provider: MarketDataProvider,
        news_provider: NewsProvider,
        technical_analyst: TechnicalAnalyst,
        synthesizer: Synthesizer,
        news_analyst: NewsAnalyst,
        recommendations_repository: RecommendationsRepository,
        runs_repository: RunsRepository,
        rationales_repository: RationalesRepository,
        console: "Console | None" = None,
        verbose: bool = False,
    ) -> None:
        self.market_data_provider = market_data_provider
        self.news_provider = news_provider
        self.technical_analyst = technical_analyst
        self.synthesizer = synthesizer
        self.news_analyst = news_analyst
        self.recommendations_repository = recommendations_repository
        self.runs_repository = runs_repository
        self.rationales_repository = rationales_repository
        self.console = console
        self.verbose = verbose

    def _log(self, message: str) -> None:
        if self.console:
            self.console.print(message)

    def _truncate_content(self, content: str, max_length: int = 2000) -> tuple[str, bool]:
        if len(content) <= max_length:
            return content, False
        truncated = content[:max_length].rsplit("\n", 1)[0]
        return truncated, True

    def _get_provider_name(self) -> str:
        provider_class_name = type(self.market_data_provider).__name__
        if provider_class_name == "OandaProvider":
            return "OANDA"
        elif provider_class_name == "TwelveDataProvider":
            return "Twelve Data"
        elif provider_class_name == "FallbackMarketDataProvider":
            return "Fallback"
        else:
            return provider_class_name.replace("Provider", "")

    def run(self, symbol: str, timeframe: Timeframe, count: int = 300) -> int:
        run = Run(
            symbol=symbol,
            timeframe=timeframe,
            start_time=datetime.now(),
            status=RunStatus.PENDING,
        )
        run_id: int | None = None

        try:
            run_id = self.runs_repository.create(run)

            provider_name = self._get_provider_name()
            self._log(f"[dim]→ Fetching market data from {provider_name}...[/dim]")
            candles = self.market_data_provider.fetch_candles(
                symbol=symbol,
                timeframe=timeframe,
                count=count,
            )

            if len(candles) < 200:
                raise ValueError(f"Insufficient candles: got {len(candles)}, need at least 200")

            self._log(f"[green]✓[/green] [dim]Loaded {len(candles)} candles[/dim]")

            self._log("[dim]→ Calculating technical indicators...[/dim]")
            indicators = calculate_features(candles)
            self._log(f"[green]✓[/green] [dim]Calculated {len(indicators)} indicators[/dim]")

            snapshot = FeatureSnapshot(
                timestamp=datetime.now(),
                candles=candles,
                indicators=indicators,
            )

            self._log("[dim]→ Running technical analysis (LLM)...[/dim]")
            technical_view, technical_llm_response = self.technical_analyst.analyze(
                snapshot, symbol, timeframe
            )
            self._log("[green]✓[/green] [dim]Technical analysis complete[/dim]")
            if self.verbose and self.console:
                from src.ui.cli.renderers.technical_renderer import render_technical_view

                display_symbol = f"{symbol[:3]}/{symbol[3:]}" if len(symbol) == 6 else symbol
                panel_title = f"Technical Rationale ({display_symbol} {timeframe.value})"

                technical_panel = render_technical_view(technical_view, title=panel_title)
                self.console.print(technical_panel)
            self.rationales_repository.save(
                Rationale(
                    run_id=run_id,
                    rationale_type=RationaleType.TECHNICAL,
                    content=technical_view,
                )
            )

            self._log("[dim]→ Fetching news context...[/dim]")
            news_digest = self.news_provider.get_news_digest(symbol, timeframe)
            self._log("[green]✓[/green] [dim]News context retrieved[/dim]")

            self._log("[dim]→ Analyzing news with LLM...[/dim]")
            news_digest, news_llm_response = self.news_analyst.analyze(news_digest)
            self._log("[green]✓[/green] [dim]News analysis complete[/dim]")

            logger.debug(
                "news_diagnostics",
                extra={
                    "symbol": symbol,
                    "timeframe": timeframe.value,
                    "provider_used": news_digest.provider_used,
                    "quality": news_digest.quality,
                    "quality_reason": news_digest.quality_reason,
                    "candidates_total": news_digest.candidates_total,
                    "articles_after_filter": news_digest.articles_after_filter,
                    "pass_counts": news_digest.pass_counts,
                    "queries_used": _sanitize_queries_used(news_digest.queries_used),
                    "gdelt_debug": _sanitize_gdelt_debug(news_digest.gdelt_debug),
                },
            )

            news_content_parts: list[str] = [f"Quality: {news_digest.quality}"]
            if news_digest.summary:
                news_content_parts.append(f"Summary: {news_digest.summary}")
            if news_digest.sentiment:
                news_content_parts.append(f"Sentiment: {news_digest.sentiment}")
            if news_digest.impact_score is not None:
                news_content_parts.append(f"Impact Score: {news_digest.impact_score:.2f}")
            if news_digest.quality_reason:
                news_content_parts.append(f"Reason: {news_digest.quality_reason}")
            if news_digest.articles:
                news_content_parts.append("Top headlines:")
                for article in news_digest.articles[:5]:
                    news_content_parts.append(f"- {article.title}")
            news_content = "\n".join(news_content_parts)

            if self.verbose and self.console:
                from rich.panel import Panel

                news_debug_enabled = _is_news_debug_enabled()
                if news_debug_enabled:
                    verbose_parts: list[str] = [news_content]
                    if news_digest.provider_used:
                        verbose_parts.append(f"\nProvider used: {news_digest.provider_used}")
                    verbose_parts.append(f"Candidates total: {news_digest.candidates_total}")
                    verbose_parts.append(f"After filtering: {news_digest.articles_after_filter}")
                    if news_digest.provider_used == "NEWSAPI" and news_digest.primary_quality:
                        verbose_parts.append(
                            f"Fallback triggered: primary {news_digest.primary_quality} -> tried NewsAPI"
                        )

                    if news_digest.pass_counts:
                        verbose_parts.append("\nPass statistics:")
                        for pass_name in ["strict", "medium", "broad"]:
                            if pass_name in news_digest.pass_counts:
                                counts = news_digest.pass_counts[pass_name]
                                verbose_parts.append(
                                    f"  {pass_name}: candidates={counts.get('candidates', 0)}, after_filter={counts.get('after_filter', 0)}"
                                )

                    if news_digest.queries_used:
                        query_items = list(news_digest.queries_used.items())[:2]
                        verbose_parts.append("\nTop queries:")
                        for tag, query in query_items:
                            query_short = query[:60] + "..." if len(query) > 60 else query
                            verbose_parts.append(f"  {tag}: {query_short}")

                    if news_digest.quality == "LOW" and news_digest.dropped_examples:
                        verbose_parts.append("\nDropped examples:")
                        for example in news_digest.dropped_examples[:3]:
                            verbose_parts.append(f"  • {example}")

                    if news_digest.gdelt_debug and news_digest.gdelt_debug.get("passes"):
                        verbose_parts.append("\nGDELT diagnostics (top requests):")
                        request_count = 0
                        for pass_name in ["strict", "medium", "broad"]:
                            if pass_name in news_digest.gdelt_debug["passes"]:
                                requests = news_digest.gdelt_debug["passes"][pass_name].get(
                                    "requests", []
                                )
                                for req in requests[:2]:
                                    if request_count >= 3:
                                        break

                                    tag = req.get("tag", "unknown")
                                    status = req.get("http_status")
                                    items = req.get("items_count", 0)

                                    error = req.get("error")
                                    json_parse_error = req.get("json_parse_error")

                                    content_type = req.get("content_type")
                                    body_length = req.get("body_length")
                                    body_preview = req.get("body_preview")

                                    if status:
                                        if status != 200:
                                            status_str = f"[red]{status}[/red]"
                                        else:
                                            status_str = f"[green]{status}[/green]"
                                    else:
                                        status_str = "?"

                                    error_str = (
                                        f", [red]error: {str(error)[:50]}[/red]" if error else ""
                                    )
                                    content_type_text = (
                                        str(content_type)[:60] if content_type else "None"
                                    )
                                    compact_line = (
                                        f"  {tag}: http_status={status_str}, content_type={content_type_text}, "
                                        f"items_count={items}{error_str}"
                                    )

                                    if json_parse_error:
                                        json_parse_error_text = str(json_parse_error)[:120]
                                        compact_line += (
                                            f", json_parse_error={json_parse_error_text}"
                                        )

                                    verbose_parts.append(compact_line)

                                    if json_parse_error and (
                                        body_length is not None or body_preview is not None
                                    ):
                                        body_length_text = (
                                            str(body_length) if body_length is not None else "None"
                                        )
                                        body_preview_text = (
                                            str(body_preview)[:200] if body_preview else "None"
                                        )
                                        verbose_parts.append(f"    body_length: {body_length_text}")
                                        verbose_parts.append(
                                            f"    body_preview: {body_preview_text}"
                                        )

                                    request_count += 1
                                if request_count >= 3:
                                    break

                    verbose_content = "\n".join(verbose_parts)
                else:
                    provider_used = news_digest.provider_used or "NONE"
                    summary_text = news_digest.summary or "N/A"

                    compact_parts: list[str] = []
                    compact_parts.append(f"Provider used: {provider_used}")
                    compact_parts.append(f"Quality: {news_digest.quality}")
                    compact_parts.append(f"Summary: {summary_text}")

                    if news_digest.quality_reason:
                        compact_parts.append(
                            f"Reason: {_truncate_single_line(news_digest.quality_reason, 180)}"
                        )

                    compact_parts.append("")
                    compact_parts.append("Top headlines:")
                    if news_digest.articles:
                        for article in news_digest.articles[:3]:
                            compact_parts.append(f"- {article.title}")
                    else:
                        compact_parts.append("  • None")

                    verbose_content = "\n".join(compact_parts)

                truncated_content, was_truncated = self._truncate_content(verbose_content)
                panel_content = truncated_content
                if was_truncated:
                    panel_content += (
                        "\n\n[dim]Use show-latest --details to view the full saved text.[/dim]"
                    )
                self.console.print(Panel(panel_content, title="News Digest", border_style="blue"))
            self.rationales_repository.save(
                Rationale(
                    run_id=run_id,
                    rationale_type=RationaleType.NEWS,
                    content=news_content,
                    raw_data=news_digest.model_dump_json(),
                )
            )

            self._log("[dim]→ Synthesizing recommendation (LLM)...[/dim]")
            recommendation, synthesis_debug, synthesis_llm_response = self.synthesizer.synthesize(
                symbol=symbol,
                timeframe=timeframe,
                technical_view=technical_view,
                news_digest=news_digest,
            )
            recommendation.run_id = run_id
            self._log("[green]✓[/green] [dim]Recommendation synthesized[/dim]")

            synthesis_content_parts: list[str] = [recommendation.brief]
            if news_digest.quality == "LOW":
                synthesis_content_parts.append("\n[System Note: News ignored due to LOW quality]")
            synthesis_content = "\n".join(synthesis_content_parts)

            raw_data_dict: dict[str, Any] = {
                "action": recommendation.action,
                "confidence": recommendation.confidence,
            }
            raw_data_dict.update(synthesis_debug)
            raw_data_json = json.dumps(raw_data_dict)

            if self.verbose and self.console:
                from src.ui.cli.renderers.synthesis_renderer import render_synthesis

                synthesis_panel = render_synthesis(
                    recommendation,
                    raw_data_json,
                    title="Synthesis Logic",
                )
                self.console.print(synthesis_panel)
            self.rationales_repository.save(
                Rationale(
                    run_id=run_id,
                    rationale_type=RationaleType.SYNTHESIS,
                    content=synthesis_content,
                    raw_data=raw_data_json,
                )
            )

            self._log("[dim]→ Saving to database...[/dim]")
            recommendation_id = self.recommendations_repository.save(recommendation)
            self._log(f"[green]✓[/green] [dim]Saved with ID: {recommendation_id}[/dim]")

            self.runs_repository.update_run(
                run_id=run_id,
                status=RunStatus.SUCCESS.value,
                end_time=datetime.now(),
                error_message=None,
            )

            return recommendation_id
        except Exception as error:
            logger.exception(
                "RunAgentsJob failed",
                extra={
                    "symbol": symbol,
                    "timeframe": timeframe.value,
                    "run_id": run_id,
                },
            )
            if run_id is not None:
                self.runs_repository.update_run(
                    run_id=run_id,
                    status=RunStatus.FAILED.value,
                    end_time=datetime.now(),
                    error_message=str(error),
                )
            raise
