from datetime import datetime
from typing import TYPE_CHECKING

from src.agents.synthesizer import Synthesizer
from src.agents.technical_analyst import TechnicalAnalyst
from src.core.models.timeframe import Timeframe
from src.core.ports.market_data_provider import MarketDataProvider
from src.core.ports.news_provider import NewsProvider
from src.features.indicators.indicator_engine import calculate_features
from src.features.snapshots.feature_snapshot import FeatureSnapshot
from src.storage.sqlite.repositories.recommendations_repository import RecommendationsRepository

if TYPE_CHECKING:
    from rich.console import Console


class RunAgentsJob:
    def __init__(
        self,
        market_data_provider: MarketDataProvider,
        news_provider: NewsProvider,
        technical_analyst: TechnicalAnalyst,
        synthesizer: Synthesizer,
        recommendations_repository: RecommendationsRepository,
        console: "Console | None" = None,
    ) -> None:
        self.market_data_provider = market_data_provider
        self.news_provider = news_provider
        self.technical_analyst = technical_analyst
        self.synthesizer = synthesizer
        self.recommendations_repository = recommendations_repository
        self.console = console

    def _log(self, message: str) -> None:
        if self.console:
            self.console.print(message)

    def run(self, symbol: str, timeframe: Timeframe, count: int = 300) -> int:
        self._log("[dim]→ Fetching market data from OANDA...[/dim]")
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

        self._log("[dim]→ Fetching news context...[/dim]")
        news_summary = self.news_provider.get_news_summary(symbol)
        self._log("[green]✓[/green] [dim]News context retrieved[/dim]")

        self._log("[dim]→ Synthesizing recommendation (LLM)...[/dim]")
        recommendation = self.synthesizer.synthesize(
            symbol=symbol,
            timeframe=timeframe,
            technical_view=technical_view,
            news_summary=news_summary,
        )
        self._log("[green]✓[/green] [dim]Recommendation synthesized[/dim]")

        self._log("[dim]→ Saving to database...[/dim]")
        recommendation_id = self.recommendations_repository.save(recommendation)
        self._log(f"[green]✓[/green] [dim]Saved with ID: {recommendation_id}[/dim]")

        return recommendation_id
