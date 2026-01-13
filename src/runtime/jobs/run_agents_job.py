from datetime import datetime
from typing import TYPE_CHECKING

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
    from rich.panel import Panel


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
            technical_view = self.technical_analyst.analyze(snapshot)
            self._log("[green]✓[/green] [dim]Technical analysis complete[/dim]")
            if self.verbose and self.console:
                from rich.panel import Panel

                truncated_content, was_truncated = self._truncate_content(technical_view)
                panel_content = truncated_content
                if was_truncated:
                    panel_content += "\n\n[dim]Use show-latest --details to view the full saved text.[/dim]"
                self.console.print(Panel(panel_content, title="Technical Rationale", border_style="cyan"))
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
            news_digest = self.news_analyst.analyze(news_digest)
            self._log("[green]✓[/green] [dim]News analysis complete[/dim]")

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

            news_summary_for_synthesizer = news_digest.summary or "No news found via GDELT."

            if self.verbose and self.console:
                from rich.panel import Panel

                truncated_content, was_truncated = self._truncate_content(news_content)
                panel_content = truncated_content
                if was_truncated:
                    panel_content += "\n\n[dim]Use show-latest --details to view the full saved text.[/dim]"
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
            recommendation = self.synthesizer.synthesize(
                symbol=symbol,
                timeframe=timeframe,
                technical_view=technical_view,
                news_summary=news_summary_for_synthesizer,
            )
            recommendation.run_id = run_id
            self._log("[green]✓[/green] [dim]Recommendation synthesized[/dim]")
            if self.verbose and self.console:
                from rich.panel import Panel

                synthesis_content = f"Action: {recommendation.action}\n"
                synthesis_content += f"Confidence: {recommendation.confidence:.2%}\n\n"
                synthesis_content += recommendation.brief
                truncated_content, was_truncated = self._truncate_content(synthesis_content)
                panel_content = truncated_content
                if was_truncated:
                    panel_content += "\n\n[dim]Use show-latest --details to view the full saved text.[/dim]"
                self.console.print(Panel(panel_content, title="Synthesis Logic", border_style="green"))
            self.rationales_repository.save(
                Rationale(
                    run_id=run_id,
                    rationale_type=RationaleType.SYNTHESIS,
                    content=recommendation.brief,
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
            if run_id is not None:
                self.runs_repository.update_run(
                    run_id=run_id,
                    status=RunStatus.FAILED.value,
                    end_time=datetime.now(),
                    error_message=str(error),
                )
            raise
