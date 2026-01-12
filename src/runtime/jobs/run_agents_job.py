from datetime import datetime

from src.agents.synthesizer import Synthesizer
from src.agents.technical_analyst import TechnicalAnalyst
from src.core.models.timeframe import Timeframe
from src.core.ports.market_data_provider import MarketDataProvider
from src.core.ports.news_provider import NewsProvider
from src.features.indicators.indicator_engine import calculate_features
from src.features.snapshots.feature_snapshot import FeatureSnapshot
from src.storage.sqlite.repositories.recommendations_repository import RecommendationsRepository


class RunAgentsJob:
    def __init__(
        self,
        market_data_provider: MarketDataProvider,
        news_provider: NewsProvider,
        technical_analyst: TechnicalAnalyst,
        synthesizer: Synthesizer,
        recommendations_repository: RecommendationsRepository,
    ) -> None:
        self.market_data_provider = market_data_provider
        self.news_provider = news_provider
        self.technical_analyst = technical_analyst
        self.synthesizer = synthesizer
        self.recommendations_repository = recommendations_repository

    def run(self, symbol: str, timeframe: Timeframe, count: int = 300) -> int:
        candles = self.market_data_provider.fetch_candles(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
        )

        if len(candles) < 200:
            raise ValueError(f"Insufficient candles: got {len(candles)}, need at least 200")

        indicators = calculate_features(candles)

        snapshot = FeatureSnapshot(
            timestamp=datetime.now(),
            candles=candles,
            indicators=indicators,
        )

        technical_view = self.technical_analyst.analyze(snapshot)

        news_summary = self.news_provider.get_news_summary(symbol)

        recommendation = self.synthesizer.synthesize(
            symbol=symbol,
            timeframe=timeframe,
            technical_view=technical_view,
            news_summary=news_summary,
        )

        recommendation_id = self.recommendations_repository.save(recommendation)

        return recommendation_id
